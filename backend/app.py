# Use eventlet for async support
import eventlet
eventlet.monkey_patch()

import os
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

# Load environment variables from .env before anything reads them
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv()  # also pick up a root-level .env if present

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, decode_token,
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the NLU engine
from nlu import NLUEngine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
log = logging.getLogger('voxa')

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
def resolve_database_uri():
    """Use the configured DATABASE_URL, but fall back to a local SQLite file
    if it points at an external server that isn't reachable. This keeps the
    app working out-of-the-box even with a placeholder .env."""
    sqlite_uri = 'sqlite:///voxa_cli.db'
    uri = os.environ.get('DATABASE_URL', '').strip()
    if not uri or uri.startswith('sqlite'):
        return uri or sqlite_uri
    try:
        from sqlalchemy import create_engine
        engine = create_engine(uri, connect_args={'connect_timeout': 2})
        with engine.connect():
            pass
        engine.dispose()
        return uri
    except Exception as e:
        log.warning("DATABASE_URL %r unreachable (%s); falling back to SQLite",
                    uri.split('@')[-1], type(e).__name__)
        return sqlite_uri


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'voxa-cli-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = resolve_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

_DEBUG = os.environ.get('FLASK_DEBUG', '0') in ('1', 'true', 'True')

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=_DEBUG,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
)


def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# JWT error handlers
# ---------------------------------------------------------------------------
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is missing'}), 401


def current_user_id():
    """JWT identity is stored as a string for cross-version safety."""
    ident = get_jwt_identity()
    try:
        return int(ident)
    except (TypeError, ValueError):
        return ident


# ---------------------------------------------------------------------------
# NLU engine
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'nlu_model.pkl')
nlu_engine = NLUEngine(model_path=MODEL_PATH)
log.info("NLU engine ready")


# ---------------------------------------------------------------------------
# Database models
# ---------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    terminal_color = db.Column(db.String(7), default='#00D9FF')
    created_at = db.Column(db.DateTime, default=utcnow)
    last_login = db.Column(db.DateTime)

    chat_sessions = db.relationship(
        'ChatSession', backref='user', lazy=True, cascade='all, delete-orphan'
    )


class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    messages = db.relationship(
        'ChatMessage', backref='session', lazy=True,
        cascade='all, delete-orphan', order_by='ChatMessage.id',
    )


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False, index=True)
    message_type = db.Column(db.String(10), nullable=False)  # 'user' | 'bot' | 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=utcnow)


with app.app_context():
    db.create_all()


def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'terminal_color': user.terminal_color,
    }


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'voxa-cli',
        'time': utcnow().isoformat(),
        'intents': list(nlu_engine.get_intents().keys()),
    }), 200


@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}

        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400

        if len(data['password']) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            terminal_color=data.get('terminal_color', '#00D9FF'),
        )
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': serialize_user(user),
        }), 201

    except Exception as e:
        db.session.rollback()
        log.exception("register failed")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}

        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400

        user = User.query.filter_by(username=data['username']).first()

        if user and check_password_hash(user.password_hash, data['password']):
            user.last_login = utcnow()
            db.session.commit()
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': serialize_user(user),
            }), 200

        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        log.exception("login failed")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = User.query.get(current_user_id())
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        **serialize_user(user),
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }), 200


@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user = User.query.get(current_user_id())
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}

        if 'terminal_color' in data:
            user.terminal_color = data['terminal_color']

        if 'email' in data:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully', 'user': serialize_user(user)}), 200

    except Exception as e:
        db.session.rollback()
        log.exception("update_profile failed")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Chat history routes
# ---------------------------------------------------------------------------
@app.route('/api/history/list', methods=['GET'])
@jwt_required()
def get_chat_history():
    user_id = current_user_id()
    sessions = (
        ChatSession.query
        .filter_by(user_id=user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return jsonify({'sessions': [{
        'id': s.id,
        'session_id': s.session_id,
        'title': s.title,
        'created_at': s.created_at.isoformat() if s.created_at else None,
        'updated_at': s.updated_at.isoformat() if s.updated_at else None,
        'message_count': len(s.messages),
    } for s in sessions]}), 200


@app.route('/api/history/<session_id>', methods=['GET'])
@jwt_required()
def get_chat_session(session_id):
    session = ChatSession.query.filter_by(
        session_id=session_id, user_id=current_user_id()
    ).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify({'session': {
        'id': session.id,
        'session_id': session.session_id,
        'title': session.title,
        'created_at': session.created_at.isoformat() if session.created_at else None,
        'updated_at': session.updated_at.isoformat() if session.updated_at else None,
        'messages': [{
            'id': m.id,
            'type': m.message_type,
            'content': m.content,
            'timestamp': m.timestamp.isoformat() if m.timestamp else None,
        } for m in session.messages],
    }}), 200


@app.route('/api/history/save', methods=['POST'])
@jwt_required()
def save_chat_session():
    try:
        user_id = current_user_id()
        data = request.get_json() or {}

        if not data.get('session_id') or data.get('messages') is None:
            return jsonify({'error': 'Missing required fields'}), 400

        session = ChatSession.query.filter_by(
            session_id=data['session_id'], user_id=user_id
        ).first()

        if session:
            session.title = data.get('title', session.title)
            session.updated_at = utcnow()
            ChatMessage.query.filter_by(session_id=session.id).delete()
        else:
            session = ChatSession(
                session_id=data['session_id'],
                user_id=user_id,
                title=data.get('title', f"Session {utcnow().strftime('%Y-%m-%d %H:%M')}"),
            )
            db.session.add(session)
            db.session.flush()

        for msg in data['messages']:
            db.session.add(ChatMessage(
                session_id=session.id,
                message_type=msg.get('type', 'user'),
                content=msg.get('content', ''),
            ))

        db.session.commit()
        return jsonify({'message': 'Chat session saved successfully', 'session_id': session.session_id}), 200

    except Exception as e:
        db.session.rollback()
        log.exception("save_chat_session failed")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    try:
        session = ChatSession.query.filter_by(
            session_id=session_id, user_id=current_user_id()
        ).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        db.session.delete(session)
        db.session.commit()
        return jsonify({'message': 'Chat session deleted'}), 200
    except Exception as e:
        db.session.rollback()
        log.exception("delete_chat_session failed")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<session_id>/rename', methods=['PUT'])
@jwt_required()
def rename_chat_session(session_id):
    try:
        session = ChatSession.query.filter_by(
            session_id=session_id, user_id=current_user_id()
        ).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        title = (request.get_json() or {}).get('title', '').strip()
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        session.title = title[:200]
        session.updated_at = utcnow()
        db.session.commit()
        return jsonify({'message': 'Renamed', 'title': session.title}), 200
    except Exception as e:
        db.session.rollback()
        log.exception("rename_chat_session failed")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Message persistence helper
# ---------------------------------------------------------------------------
def persist_exchange(user_id, session_id, user_text, bot_text):
    """Persist a user/bot exchange to the DB (best-effort)."""
    if not user_id:
        return
    try:
        session = ChatSession.query.filter_by(
            session_id=session_id, user_id=user_id
        ).first()
        if not session:
            title = (user_text[:60] + '…') if len(user_text) > 60 else user_text
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=title or f"Session {utcnow().strftime('%Y-%m-%d %H:%M')}",
            )
            db.session.add(session)
            db.session.flush()
        else:
            session.updated_at = utcnow()

        db.session.add(ChatMessage(session_id=session.id, message_type='user', content=user_text))
        db.session.add(ChatMessage(session_id=session.id, message_type='bot', content=bot_text))
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("persist_exchange failed")


# ---------------------------------------------------------------------------
# WebSocket events
# ---------------------------------------------------------------------------
socket_users = {}  # sid -> user_id


@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to Voxa CLI server'})


@socketio.on('disconnect')
def handle_disconnect():
    socket_users.pop(request.sid, None)


@socketio.on('authenticate')
def handle_authenticate(data):
    try:
        token = (data or {}).get('token')
        if not token:
            emit('auth_error', {'message': 'No token provided'})
            return
        try:
            decoded = decode_token(token)
            user_id = decoded['sub']
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                pass
            user = User.query.get(user_id)
            if user:
                socket_users[request.sid] = user.id
                join_room(f"user_{user.id}")
                emit('authenticated', {
                    'message': f'Welcome back, {user.username}!',
                    'user': serialize_user(user),
                })
            else:
                emit('auth_error', {'message': 'User not found'})
        except Exception:
            emit('auth_error', {'message': 'Invalid token'})
    except Exception as e:
        emit('auth_error', {'message': str(e)})


@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        if not data:
            emit('error', {'message': 'No data received'})
            return

        user_input = (data.get('message') or '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())

        if not user_input:
            emit('error', {'message': 'Empty message. Please type something.'})
            return
        if len(user_input) > 5000:
            emit('error', {'message': 'Message too long. Keep it under 5000 characters.'})
            return

        # Let the client show a typing indicator immediately
        emit('bot_typing', {'session_id': session_id})

        try:
            user_id = socket_users.get(request.sid) or data.get('user_id')
            nlu_result = nlu_engine.process(user_input, session_id, user_id)
            bot_response = nlu_result.get('response') or \
                "I'm sorry, I couldn't generate a response. Please try again."
        except Exception:
            log.exception("NLU processing error")
            bot_response = "I encountered an error processing your request. Please try again."
            nlu_result = {'intent': {'intent': 'error', 'confidence': 0.0},
                          'entities': {}, 'metadata': {}}

        emit('bot_response', {
            'type': 'bot',
            'content': bot_response,
            'timestamp': utcnow().isoformat(),
            'session_id': session_id,
            'nlu_data': {
                'intent': nlu_result.get('intent', {}).get('intent', 'unknown'),
                'confidence': nlu_result.get('intent', {}).get('confidence', 0.0),
                'method': nlu_result.get('intent', {}).get('method', ''),
                'entities': nlu_result.get('entities', {}).get('normalized', {}),
                'all_scores': nlu_result.get('intent', {}).get('all_scores', {}),
                'sentiment': nlu_result.get('sentiment', {}),
                'action': nlu_result.get('action_result', {}).get('action', ''),
            },
        })

        # Persist the exchange for authenticated users (best-effort)
        uid = socket_users.get(request.sid)
        if uid:
            persist_exchange(uid, session_id, user_input, bot_response)

    except KeyError as e:
        emit('error', {'message': f'Invalid message format: missing {str(e)}'})
    except Exception:
        log.exception("chat handler error")
        emit('error', {'message': 'An unexpected error occurred. Please try again.'})


@socketio.on('voice_input')
def handle_voice_input(data):
    try:
        if not data or not data.get('audio'):
            emit('error', {'message': 'No audio data in voice input'})
            return
        emit('voice_processed', {
            'message': 'Voice input received',
            'session_id': data.get('session_id', str(uuid.uuid4())),
            'timestamp': utcnow().isoformat(),
        })
    except Exception:
        log.exception("voice handler error")
        emit('error', {'message': 'Failed to process voice input. Please try again.'})


# ---------------------------------------------------------------------------
# Admin / NLU management routes
# ---------------------------------------------------------------------------
@app.route('/api/admin/intents', methods=['GET'])
@jwt_required()
def get_intents():
    try:
        return jsonify({'success': True, 'intents': nlu_engine.get_intents()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/training-data', methods=['GET'])
@jwt_required()
def get_training_data():
    try:
        return jsonify({'success': True, 'training_data': nlu_engine.get_training_data()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/training-data', methods=['POST'])
@jwt_required()
def add_training_data():
    try:
        data = request.get_json() or {}
        intent = data.get('intent')
        utterances = data.get('utterances', [])
        if not intent or not utterances:
            return jsonify({'success': False, 'error': 'Intent and utterances are required'}), 400
        nlu_engine.add_training_data(intent, utterances)
        return jsonify({'success': True, 'message': f'Added {len(utterances)} utterances to {intent}'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/retrain', methods=['POST'])
@jwt_required()
def retrain_model():
    try:
        nlu_engine.retrain()
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        nlu_engine.save_model(MODEL_PATH)
        return jsonify({'success': True, 'message': 'Model retrained successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/session-stats/<session_id>', methods=['GET'])
@jwt_required()
def get_session_stats(session_id):
    try:
        stats = nlu_engine.get_session_stats(session_id)
        if not stats:
            return jsonify({'success': False, 'error': 'Session not found or expired'}), 404
        return jsonify({'success': True, 'stats': stats}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/nlu/analyze', methods=['POST'])
@jwt_required()
def analyze_text():
    try:
        text = (request.get_json() or {}).get('text')
        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        result = nlu_engine.process(text, f"test_{uuid.uuid4()}")
        return jsonify({'success': True, 'analysis': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    log.info("Starting Voxa CLI server on :5000")
    socketio.run(app, debug=_DEBUG, host='0.0.0.0', port=5000)

#!/usr/bin/env python3
"""
ESP32 Battery Monitor Server
Provides real-time EV battery data via HTTP API
Compatible with ESP32 WiFi configuration
"""

import asyncio
import json
import random
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'esp32-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ESP32 device configuration
ESP32_IP = '192.168.4.1'  # Default ESP32 IP in AP mode
ESP32_BASE_URL = f'http://{ESP32_IP}'

# Global configuration
config = {
    'esp32_ip': ESP32_IP,
    'last_update': datetime.now().isoformat(),
    'connection_status': 'disconnected'
}

@app.route('/api/esp32/config', methods=['POST'])
def configure_esp32():
    """Configure ESP32 WiFi settings"""
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')
    device_name = data.get('device_name', 'ESP32-Battery')
    
    # Send configuration to ESP32
    try:
        response = requests.post(
            f"{ESP32_BASE_URL}/wifi/configure",
            json={'ssid': ssid, 'password': password, 'device_name': device_name},
            timeout=5
        )
        return jsonify({'success': True, 'response': response.json()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/esp32/scan', methods=['GET'])
def scan_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        response = requests.get(f"{ESP32_BASE_URL}/wifi/scan", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'networks': [], 'error': str(e)}), 500

@app.route('/api/battery', methods=['GET'])
def get_battery_data():
    """Get battery data from ESP32"""
    try:
        response = requests.get(f"{ESP32_BASE_URL}/api/battery", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        # Fallback to mock data if ESP32 unavailable
        return jsonify({
            'data': {
                'voltage': 12.8,
                'current': 2.1,
                'temperature': 35.6,
                'soc': 83,
                'soh': 97,
                'fault_flags': [],
                'timestamp': datetime.now().isoformat()
            },
            'source': 'mock',
            'error': str(e)
        })

@app.route('/api/battery/history', methods=['GET'])
def get_battery_history():
    """Get historical battery data from ESP32"""
    try:
        limit = request.args.get('limit', 100)
        response = requests.get(f"{ESP32_BASE_URL}/api/history?limit={limit}", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        # Fallback to mock data
        return jsonify({
            'data': [],
            'source': 'mock',
            'error': str(e)
        })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'esp32_ip': config['esp32_ip'],
        'last_update': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting ESP32 Battery Monitor Server...")
    print("WiFi Configuration available at: http://localhost:5000/api/esp32/config")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

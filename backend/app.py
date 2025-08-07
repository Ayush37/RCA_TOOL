from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from services.metric_loader import MetricLoader
from services.rca_analyzer import RCAAnalyzer

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Choose authentication method based on environment variable
auth_method = os.getenv('AUTH_METHOD', 'api_key').lower()

if auth_method == 'certificate':
    logger.info("Using certificate-based authentication for Azure OpenAI")
    from services.azure_ai_service_cert import AzureAIServiceCert
    ai_service = AzureAIServiceCert()
else:
    logger.info("Using API key authentication for Azure OpenAI")
    from services.azure_ai_service import AzureAIService
    ai_service = AzureAIService()

metric_loader = MetricLoader()
rca_analyzer = RCAAnalyzer()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'metric_loader': 'ready',
            'rca_analyzer': 'ready',
            'azure_ai': ai_service.is_configured()
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_query = data.get('query', '')
        target_date = data.get('date', '2025-08-01')
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        logger.info(f"Processing query: {user_query} for date: {target_date}")
        
        metrics = metric_loader.load_all_metrics(target_date)
        if not metrics:
            return jsonify({
                'error': f'No metrics found for date {target_date}',
                'available_dates': metric_loader.get_available_dates()
            }), 404
        
        analysis = rca_analyzer.analyze(metrics, target_date)
        
        ai_response = ai_service.generate_response(
            analysis=analysis,
            user_query=user_query,
            metrics=metrics
        )
        
        response = {
            'analysis': ai_response,
            'timeline': analysis['timeline'],
            'metrics_summary': analysis['metrics_summary'],
            'sla_status': analysis['sla_status'],
            'root_causes': analysis['root_causes'],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/detailed', methods=['POST'])
def chat_detailed():
    """Enhanced endpoint that returns step-by-step analysis details"""
    try:
        data = request.json
        user_query = data.get('query', '')
        target_date = data.get('date', '2025-08-01')
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        logger.info(f"Processing detailed query: {user_query} for date: {target_date}")
        
        # Step 1: Load metrics
        metrics = metric_loader.load_all_metrics(target_date)
        if not metrics:
            return jsonify({
                'error': f'No metrics found for date {target_date}',
                'available_dates': metric_loader.get_available_dates()
            }), 404
        
        # Step 2: Extract key information for steps
        marker_info = None
        if metrics.get('markerEvent'):
            marker = metrics['markerEvent']
            marker_info = {
                'arrival_time': marker.get('actual_arrival_time'),
                'expected_time': marker.get('expected_arrival_time'),
                'delay_minutes': marker.get('delay_in_minutes', 0),
                'product': marker.get('product')
            }
        
        # Step 3: Perform analysis
        analysis = rca_analyzer.analyze(metrics, target_date)
        
        # Step 4: Get AI response
        ai_response = ai_service.generate_response(
            analysis=analysis,
            user_query=user_query,
            metrics=metrics
        )
        
        # Create detailed response with steps
        response = {
            'steps': {
                'marker_check': {
                    'status': 'complete',
                    'data': marker_info
                },
                'dag_analysis': {
                    'status': 'complete',
                    'data': {
                        'start_time': analysis['sla_status'].get('arrival_time') if analysis.get('sla_status') else None,
                        'end_time': analysis['sla_status'].get('completion_time') if analysis.get('sla_status') else None,
                        'duration': analysis.get('processing_duration')
                    }
                },
                'infrastructure_check': {
                    'status': 'complete',
                    'data': analysis.get('metrics_summary')
                }
            },
            'analysis': ai_response,
            'timeline': analysis['timeline'],
            'metrics_summary': analysis['metrics_summary'],
            'sla_status': analysis['sla_status'],
            'root_causes': analysis['root_causes'],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing detailed chat request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/<date>', methods=['GET'])
def get_metrics(date):
    try:
        metrics = metric_loader.load_all_metrics(date)
        if not metrics:
            return jsonify({
                'error': f'No metrics found for date {date}',
                'available_dates': metric_loader.get_available_dates()
            }), 404
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error loading metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/available-dates', methods=['GET'])
def get_available_dates():
    try:
        dates = metric_loader.get_available_dates()
        return jsonify({'dates': dates})
    except Exception as e:
        logger.error(f"Error getting available dates: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
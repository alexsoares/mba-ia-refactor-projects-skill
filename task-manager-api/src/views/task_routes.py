from flask import Blueprint, jsonify, request


def create_task_blueprint(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.get('/tasks')
    def get_tasks():
        return jsonify(controller.list()), 200

    @task_bp.get('/tasks/<int:task_id>')
    def get_task(task_id):
        return jsonify(controller.get(task_id)), 200

    @task_bp.post('/tasks')
    def create_task():
        return jsonify(controller.create(request.get_json(silent=True))), 201

    @task_bp.put('/tasks/<int:task_id>')
    def update_task(task_id):
        return jsonify(controller.update(task_id, request.get_json(silent=True))), 200

    @task_bp.delete('/tasks/<int:task_id>')
    def delete_task(task_id):
        controller.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @task_bp.get('/tasks/search')
    def search_tasks():
        args = request.args
        return jsonify(controller.search(args.get('q', ''), args.get('status', ''),
                                         args.get('priority', ''), args.get('user_id', ''))), 200

    @task_bp.get('/tasks/stats')
    def task_stats():
        return jsonify(controller.stats()), 200

    return task_bp

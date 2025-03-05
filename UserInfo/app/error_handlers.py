from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(400)
    def handle_400_error(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def handle_404_error(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_500_error(error):
        return jsonify({"error": "Internal server error"}), 500

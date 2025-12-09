from app import create_app
from app.services.graph_loader import GraphLoader

app = create_app()

if __name__ == '__main__':
    # Tải trước bản đồ khi khởi động Server
    with app.app_context():
        print("dang khoi tao...")
        GraphLoader.get_graph()
        
    app.run(debug=True, port=5000)

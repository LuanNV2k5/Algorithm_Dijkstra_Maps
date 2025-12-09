import os

# Cấu trúc dự án và nội dung file
project_structure = {
    "requirements.txt": """flask
osmnx
networkx
scikit-learn
""",
    "run.py": """from app import create_app
from app.services.graph_loader import GraphLoader

app = create_app()

if __name__ == '__main__':
    # Tải trước bản đồ khi khởi động Server
    with app.app_context():
        print("dang khoi tao...")
        GraphLoader.get_graph()
        
    app.run(debug=True, port=5000)
""",
    "app/__init__.py": """from flask import Flask

def create_app():
    app = Flask(__name__)
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
""",
    "app/routes.py": """from flask import Blueprint, render_template, request, jsonify
import osmnx as ox
from app.services.graph_loader import GraphLoader
from app.services.algorithms import GraphAlgorithms

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/find-path', methods=['POST'])
def find_path():
    try:
        data = request.json
        points = data.get('points')
        
        if not points or len(points) < 2:
            return jsonify({'success': False, 'message': 'Cần ít nhất 2 điểm!'})

        G = GraphLoader.get_graph()
        full_route_coords = []

        # Tìm đường qua từng cặp điểm
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            # ox.distance.nearest_nodes nhận tham số (lng, lat)
            node_start = ox.distance.nearest_nodes(G, p1[1], p1[0])
            node_end = ox.distance.nearest_nodes(G, p2[1], p2[0])
            
            path_nodes = GraphAlgorithms.custom_dijkstra(G, node_start, node_end)
            
            if not path_nodes:
                return jsonify({'success': False, 'message': 'Không tìm thấy đường đi!'})

            # Chuyển đổi Node ID sang tọa độ [lat, lng]
            segment_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in path_nodes]
            
            if i > 0:
                full_route_coords.extend(segment_coords[1:])
            else:
                full_route_coords.extend(segment_coords)

        return jsonify({'success': True, 'route': full_route_coords})

    except Exception as e:
        print(f"Lỗi: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
""",
    "app/services/__init__.py": "",
    "app/services/graph_loader.py": """import osmnx as ox
import os

class GraphLoader:
    _graph = None
    # Chọn khu vực nhỏ: Phường Bến Nghé, Quận 1
    PLACE_NAME = "Ben Nghe Ward, District 1, Ho Chi Minh City, Vietnam"
    CACHE_FILE = "graph_cache.graphml"

    @classmethod
    def get_graph(cls):
        if cls._graph is None:
            if os.path.exists(cls.CACHE_FILE):
                print("⚡ Đang tải bản đồ từ Cache...")
                cls._graph = ox.load_graphml(cls.CACHE_FILE)
            else:
                print("🌍 Đang tải bản đồ từ Internet (Lần đầu sẽ lâu)...")
                cls._graph = ox.graph_from_place(cls.PLACE_NAME, network_type='drive')
                
                # Gán trọng số weight = length nếu chưa có
                for u, v, data in cls._graph.edges(data=True):
                    if 'weight' not in data:
                        data['weight'] = data.get('length', 1)

                ox.save_graphml(cls._graph, cls.CACHE_FILE)
                print("✅ Đã lưu cache bản đồ.")
        return cls._graph
""",
    "app/services/algorithms.py": """import heapq

class GraphAlgorithms:
    @staticmethod
    def custom_dijkstra(graph, start_node, end_node):
        pq = [(0, start_node)]
        distances = {node: float('inf') for node in graph.nodes}
        distances[start_node] = 0
        previous = {node: None for node in graph.nodes}
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node == end_node:
                break
                
            if current_dist > distances[current_node]:
                continue
            
            for neighbor in graph.neighbors(current_node):
                # Lấy cạnh có độ dài nhỏ nhất giữa 2 node
                edge_data = min(graph.get_edge_data(current_node, neighbor).values(), 
                              key=lambda x: x.get('length', 1))
                weight = edge_data.get('weight', edge_data.get('length', 1))
                
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        
        path = []
        curr = end_node
        if previous[curr] is None and curr != start_node:
            return None
            
        while curr is not None:
            path.append(curr)
            curr = previous[curr]
            
        return path[::-1]
""",
    "app/templates/index.html": """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đồ án Tìm đường Du lịch</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>Du lịch Thông minh</h2>
            <p>Click bản đồ để chọn điểm.</p>
            <ul id="points-list"></ul>
            <div class="buttons">
                <button onclick="findPath()" class="btn-primary">Tìm đường (Dijkstra)</button>
                <button onclick="resetMap()" class="btn-secondary">Làm mới</button>
            </div>
            <div id="status"></div>
        </div>
        <div id="map"></div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
""",
    "app/static/css/style.css": """body { margin: 0; padding: 0; display: flex; height: 100vh; font-family: Arial, sans-serif; }
.container { display: flex; width: 100%; }
.sidebar { width: 300px; padding: 20px; background: #f8f9fa; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
#map { flex-grow: 1; height: 100vh; }
.buttons { margin-top: 20px; display: flex; gap: 10px; }
button { padding: 10px; border: none; cursor: pointer; border-radius: 5px; color: white; flex: 1; }
.btn-primary { background: #007bff; }
.btn-secondary { background: #6c757d; }
#points-list { list-style: none; padding: 0; margin-top: 20px; overflow-y: auto; flex-grow: 1; }
#points-list li { padding: 10px; border-bottom: 1px solid #eee; }
""",
    "app/static/js/main.js": """const map = L.map('map').setView([10.7797, 106.7001], 15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let markers = [];
let selectedPoints = [];
let polyline = null;

map.on('click', function(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    const marker = L.marker([lat, lng]).addTo(map);
    marker.bindPopup(`Điểm ${markers.length + 1}`).openPopup();
    markers.push(marker);
    selectedPoints.push([lat, lng]);
    updateSidebar();
});

function updateSidebar() {
    document.getElementById('points-list').innerHTML = markers.map((_, index) => `<li>📍 Điểm số ${index + 1}</li>`).join('');
}

async function findPath() {
    const statusDiv = document.getElementById('status');
    if (selectedPoints.length < 2) {
        statusDiv.innerHTML = "<span style='color:red'>Chọn ít nhất 2 điểm!</span>";
        return;
    }
    statusDiv.innerHTML = "⏳ Đang tính toán...";
    try {
        const response = await fetch('/api/find-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ points: selectedPoints })
        });
        const data = await response.json();
        if (data.success) {
            statusDiv.innerHTML = "<span style='color:green'>Xong!</span>";
            if (polyline) map.removeLayer(polyline);
            polyline = L.polyline(data.route, {color: 'blue', weight: 5}).addTo(map);
            map.fitBounds(polyline.getBounds());
        } else {
            statusDiv.innerHTML = `<span style='color:red'>Lỗi: ${data.message}</span>`;
        }
    } catch (error) {
        console.error(error);
        statusDiv.innerHTML = "<span style='color:red'>Lỗi server!</span>";
    }
}

function resetMap() {
    markers.forEach(m => map.removeLayer(m));
    if (polyline) map.removeLayer(polyline);
    markers = [];
    selectedPoints = [];
    updateSidebar();
    document.getElementById('status').innerHTML = "";
}
"""
}

def create_project():
    print("🚀 Đang khởi tạo cấu trúc dự án...")
    for filepath, content in project_structure.items():
        # Tạo thư mục cha nếu chưa có
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # Ghi file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Đã tạo: {filepath}")
    
    print("\n🎉 Hoàn tất! Cấu trúc dự án đã sẵn sàng.")
    print("👉 Hãy chạy lệnh: pip install -r requirements.txt")
    print("👉 Sau đó chạy: python run.py")

if __name__ == "__main__":
    create_project()
from flask import Blueprint, render_template, request, jsonify
import osmnx as ox
from app.services.graph_loader import GraphLoader
from app.services.algorithms import GraphAlgorithms
import itertools # Thư viện để tạo hoán vị các điểm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/find-path', methods=['POST'])
def find_path():
    try:
        data = request.json
        points = data.get('points') # Danh sách tọa độ [ [lat, lng], ... ]
        
        if not points or len(points) < 2:
            return jsonify({'success': False, 'message': 'Cần ít nhất 2 điểm!'})

        G = GraphLoader.get_graph()
        
        # 1. CHUYỂN ĐỔI TỌA ĐỘ GPS SANG NODE ID TRÊN ĐỒ THỊ
        # Chúng ta làm bước này trước để không phải tìm lại nhiều lần
        input_nodes = []
        for p in points:
            # Lưu ý: osmnx dùng (lng, lat), leaflet gửi (lat, lng)
            node = ox.distance.nearest_nodes(G, p[1], p[0])
            input_nodes.append(node)

        start_node = input_nodes[0]       # Điểm xuất phát cố định (Điểm số 1)
        destinations = input_nodes[1:]    # Các điểm cần ghé thăm (Điểm 2, 3...)

        # 2. TÍNH TOÁN MA TRẬN KHOẢNG CÁCH (CACHE)
        # Để tránh chạy Dijkstra lặp lại cho cùng 1 đoạn đường, ta lưu vào cache
        # Key: (node_A, node_B) -> Value: { 'path': [...], 'dist': 1200.5 }
        segment_cache = {}

        def get_segment_data(u, v):
            # Nếu đã tính rồi thì lấy trong cache ra dùng
            if (u, v) in segment_cache:
                return segment_cache[(u, v)]
            
            # Nếu chưa thì chạy Dijkstra
            path_nodes = GraphAlgorithms.custom_dijkstra(G, u, v)
            
            if not path_nodes:
                return None

            # Tính độ dài đoạn này
            dist = 0
            for i in range(len(path_nodes) - 1):
                n1, n2 = path_nodes[i], path_nodes[i+1]
                edges = G.get_edge_data(n1, n2)
                if edges:
                    best_edge = min(edges.values(), key=lambda x: x.get('length', float('inf')))
                    dist += best_edge.get('length', 0) # weight đã ép kiểu float ở graph_loader
            
            # Lưu vào cache
            result = {'path': path_nodes, 'dist': dist}
            segment_cache[(u, v)] = result
            return result

        # 3. TÌM THỨ TỰ ĐI TỐI ƯU (TSP - BRUTE FORCE)
        # Tạo tất cả các trường hợp hoán đổi thứ tự các điểm đến
        # Ví dụ: (2, 3), (3, 2)...
        best_order = None
        min_total_dist = float('inf')

        possible_orders = list(itertools.permutations(destinations))

        for order in possible_orders:
            # Tạo lộ trình thử nghiệm: Start -> A -> B -> ...
            current_route_sequence = [start_node] + list(order)
            current_total_dist = 0
            valid_order = True

            # Tính tổng khoảng cách của lộ trình này
            for i in range(len(current_route_sequence) - 1):
                u = current_route_sequence[i]
                v = current_route_sequence[i+1]
                
                seg_data = get_segment_data(u, v)
                if seg_data is None:
                    valid_order = False
                    break
                current_total_dist += seg_data['dist']
            
            # Nếu lộ trình này hợp lệ và ngắn hơn kỷ lục trước đó -> Cập nhật
            if valid_order and current_total_dist < min_total_dist:
                min_total_dist = current_total_dist
                best_order = current_route_sequence

        if best_order is None:
             return jsonify({'success': False, 'message': 'Không tìm thấy đường đi nối các điểm này!'})

        # 4. TẠO DỮ LIỆU TRẢ VỀ CHO WEB TỪ LỘ TRÌNH TỐI ƯU NHẤT
        full_route_coords = []
        route_details = []
        final_total_dist = 0

        # Mapping lại Node ID sang tên hiển thị (Ví dụ: Node 123 -> "Điểm số 2")
        # Ta cần biết Node ID nào ứng với Điểm số mấy ban đầu của người dùng
        node_to_label = {}
        for idx, node in enumerate(input_nodes):
            # Lưu ý: Nếu user chọn 2 điểm trùng nhau thì logic này cần cải thiện, 
            # nhưng với demo thì ổn.
            node_to_label[node] = f"Điểm số {idx + 1}"

        for i in range(len(best_order) - 1):
            u = best_order[i]
            v = best_order[i+1]
            
            data = get_segment_data(u, v) # Chắc chắn có vì đã check ở trên
            
            # Tạo thông tin chi tiết
            label_from = node_to_label.get(u, "Điểm TG")
            label_to = node_to_label.get(v, "Điểm TG")

            route_details.append({
                "step": i + 1,
                "from": label_from,
                "to": label_to,
                "distance": round(data['dist'], 2)
            })
            final_total_dist += data['dist']

            # Lấy tọa độ vẽ
            path_nodes = data['path']
            segment_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in path_nodes]

            if i > 0:
                full_route_coords.extend(segment_coords[1:])
            else:
                full_route_coords.extend(segment_coords)

        return jsonify({
            'success': True,
            'route': full_route_coords,
            'details': route_details,
            'total_dist': round(final_total_dist, 2)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
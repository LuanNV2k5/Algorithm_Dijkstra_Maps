import osmnx as ox
import networkx as nx # Cần thêm thư viện này để xử lý kết nối
import os

class GraphLoader:
    _graph = None
    # Tọa độ trung tâm (Nhà thờ Đức Bà)
    CENTER_POINT = (10.77978, 106.69902) 
    # --- TĂNG BÁN KÍNH LÊN 3000m (3km) ---
    DIST = 3000 
    CACHE_FILE = "graph_cache.graphml"

    @classmethod
    def get_graph(cls):
        if cls._graph is None:
            if os.path.exists(cls.CACHE_FILE):
                print("⚡ Đang tải bản đồ từ Cache...")
                cls._graph = ox.load_graphml(cls.CACHE_FILE)
            else:
                print(f"🌍 Đang tải bản đồ bán kính {cls.DIST}m từ Internet (Sẽ hơi lâu)...")
                # 1. Tải bản đồ thô
                G_raw = ox.graph_from_point(cls.CENTER_POINT, dist=cls.DIST, network_type='drive')
                
                print("🔧 Đang xử lý dữ liệu đường bộ (Lọc vùng kết nối lớn nhất)...")
                # 2. BƯỚC QUAN TRỌNG MỚI: Chỉ giữ lại thành phần kết nối mạnh lớn nhất
                # Điều này đảm bảo từ mọi điểm A đều có thể đi đến B và ngược lại
                # (Tránh các khu vực bị cô lập bởi đường 1 chiều)
                largest_cc = max(nx.strongly_connected_components(G_raw), key=len)
                cls._graph = G_raw.subgraph(largest_cc).copy()
                
                # 3. Làm sạch dữ liệu trọng số (như cũ)
                for u, v, k, data in cls._graph.edges(keys=True, data=True):
                    raw_length = data.get('length', 10)
                    if isinstance(raw_length, list):
                        raw_length = raw_length[0]
                    try:
                        data['weight'] = float(raw_length)
                    except (ValueError, TypeError):
                        data['weight'] = 10.0

                ox.save_graphml(cls._graph, cls.CACHE_FILE)
                print(f"✅ Đã xử lý xong và lưu cache. Số đỉnh: {len(cls._graph.nodes)}")
        return cls._graph
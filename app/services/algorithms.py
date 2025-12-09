import heapq

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
                # Lấy dữ liệu cạnh
                edge_data = min(graph.get_edge_data(current_node, neighbor).values(), 
                              key=lambda x: float(x.get('length', 1))) # Ép kiểu float ở đây
                
                # --- SỬA LỖI ---
                try:
                    # Ưu tiên lấy 'weight', nếu không có thì lấy 'length', ép sang float
                    weight = float(edge_data.get('weight', edge_data.get('length', 1)))
                except:
                    weight = 1.0

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
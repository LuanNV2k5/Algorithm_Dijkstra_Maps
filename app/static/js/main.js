// Cấu hình bản đồ trung tâm
const map = L.map('map').setView([10.7797, 106.7001], 15);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let markers = [];
let selectedPoints = [];
let polyline = null;

// Sự kiện click bản đồ
map.on('click', function(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // Thêm marker
    const marker = L.marker([lat, lng]).addTo(map);
    marker.bindPopup(`Điểm ${markers.length + 1}`).openPopup();
    
    markers.push(marker);
    selectedPoints.push([lat, lng]);

    // Cập nhật giao diện list
    updateSidebar();
});

function updateSidebar() {
    const list = document.getElementById('points-list');
    list.innerHTML = markers.map((_, index) => `<li>📍 Điểm số ${index + 1}</li>`).join('');
}

async function findPath() {
    const statusDiv = document.getElementById('status');
    const detailsDiv = document.getElementById('route-details'); // Khu vực hiển thị chữ
    
    if (selectedPoints.length < 2) {
        statusDiv.innerHTML = "<span style='color:red'>Vui lòng chọn ít nhất 2 điểm!</span>";
        return;
    }

    statusDiv.innerHTML = "⏳ Đang tính toán...";
    detailsDiv.innerHTML = "<p>Đang tải dữ liệu...</p>";

    try {
        const response = await fetch('/api/find-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ points: selectedPoints })
        });

        const data = await response.json();

        if (data.success) {
            statusDiv.innerHTML = "<span style='color:green'>Đã tìm thấy đường đi!</span>";
            
            // 1. VẼ ĐƯỜNG LÊN BẢN ĐỒ
            if (polyline) map.removeLayer(polyline);

            polyline = L.polyline(data.route, {
                color: '#007bff', 
                weight: 6,
                opacity: 0.8
            }).addTo(map);
            
            map.fitBounds(polyline.getBounds());

            // 2. HIỂN THỊ CHI TIẾT LỘ TRÌNH (TEXT)
            let htmlHTML = `<div style="margin-bottom: 10px; font-weight: bold; color: #d63384;">
                                🏁 Tổng quãng đường: ${(data.total_dist / 1000).toFixed(2)} km
                            </div>`;
            
            htmlHTML += `<ul style="padding-left: 20px; list-style-type: circle;">`;
            
            data.details.forEach(step => {
                htmlHTML += `
                    <li style="margin-bottom: 8px; font-size: 14px;">
                        <strong>Chặng ${step.step}:</strong> ${step.from} ➝ ${step.to} <br>
                        <span style="color: blue;">➡ Dài: ${step.distance} mét</span>
                    </li>
                `;
            });
            htmlHTML += `</ul>`;
            
            detailsDiv.innerHTML = htmlHTML;

        } else {
            statusDiv.innerHTML = `<span style='color:red'>Lỗi: ${data.message}</span>`;
            detailsDiv.innerHTML = "<p style='color:red'>Không có dữ liệu.</p>";
        }
    } catch (error) {
        console.error(error);
        statusDiv.innerHTML = "<span style='color:red'>Lỗi kết nối server!</span>";
        detailsDiv.innerHTML = "";
    }
}

function resetMap() {
    markers.forEach(m => map.removeLayer(m));
    if (polyline) map.removeLayer(polyline);
    markers = [];
    selectedPoints = [];
    updateSidebar();
    document.getElementById('status').innerHTML = "";
    document.getElementById('route-details').innerHTML = "<p style='color: #666; font-style: italic; font-size: 0.9em;'>Chưa có lộ trình nào.</p>";
}
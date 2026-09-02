import json, urllib.request, math

def get_trace(shape):
    req = urllib.request.Request('http://localhost:8002/trace_attributes', data=json.dumps({'shape': shape, 'costing': 'auto', 'shape_match': 'map_snap'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    return res.get('edges', [])

c_start = {'lat': 14.55998, 'lon': 121.07722}
c_end = {'lat': 14.56066, 'lon': 121.07826}

edges = get_trace([c_start, c_end])
print(f\"Original Road: {edges[0].get('names') if edges else None}, Traversability: {edges[0].get('traversability') if edges else None}\")

earth_radius = 6378137.0
dy = c_end['lat'] - c_start['lat']
dx = c_end['lon'] - c_start['lon']
angle = math.atan2(dy, dx)
left_angle = angle + (math.pi / 2)
lat_offset = (15.0 / earth_radius) * (180.0 / math.pi)
lon_offset = (15.0 / (earth_radius * math.cos(math.pi * c_start['lat'] / 180.0))) * (180.0 / math.pi)

shifted_start = {'lat': c_end['lat'] + math.sin(left_angle) * lat_offset, 'lon': c_end['lon'] + math.cos(left_angle) * lon_offset}
shifted_end = {'lat': c_start['lat'] + math.sin(left_angle) * lat_offset, 'lon': c_start['lon'] + math.cos(left_angle) * lon_offset}

opp_edges = get_trace([shifted_start, shifted_end])
print(f\"Opposite Road: {opp_edges[0].get('names') if opp_edges else None}, Traversability: {opp_edges[0].get('traversability') if opp_edges else None}\")

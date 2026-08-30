# **Architectural Analysis of Routing Engines for Flood-Resilient Progressive Web Applications in the Philippines**

The development of disaster-resilient routing systems for mobile architectures demands a fundamental reevaluation of standard geographic information system (GIS) frameworks. When operating in environments characterized by complex, non-linear urban planning and acute environmental hazards—such as typhoon-induced flooding in the Philippines—traditional routing engines frequently fail to deliver viable paths. The proposal to transition the backend, frontend, and database layers of a flood-navigation Progressive Web Application (PWA) away from Valhalla in favor of a dual-engine architecture utilizing GraphHopper for online routing and BRouter for offline capabilities is highly sound.  
This report provides an exhaustive, expert-level architectural analysis of this transition. It explores the algorithmic mechanics of OpenStreetMap (OSM) parsing, the computational limitations of various open-source routing tools, the viability of client-side WebAssembly (WASM) execution, and the overarching data storage strategies required to persist massive graph networks within a browser's local environment.

## **The Philippine Urban Spatial Context and OpenStreetMap Topology**

Before analyzing the software layers, it is necessary to understand the geographic and cartographic data structures upon which these routing engines operate. The Philippines presents a highly irregular urban topography. Unlike grid-based cities in Western contexts, Philippine urban centers are characterized by dense networks of informal roads, alleys (esquinitas), undocumented tertiary streets, and rapid transitions between paved and unpaved surfaces.  
Within the OpenStreetMap (OSM) ecosystem, road qualities are largely defined by tags such as highway=\*, surface=\*, and tracktype=\*. The tracktype tag, which ranges from grade1 (solid, paved) to grade5 (soft, unpaved, often impassable in severe weather), is particularly critical in developing nations where informal infrastructure is prevalent. Routing engines parse these tags to compute edge weights and traverse the geographic graph using search algorithms such as Dijkstra or A\*. However, the rigidity with which a routing engine interprets these tags determines its efficacy in complex topographies.

### **Evaluation of Valhalla in Developing Topographies**

Valhalla is a highly capable, open-source routing engine that utilizes dynamic, tile-based costing models. It is widely deployed for multimodal transit and enterprise-scale logistics1. Despite its strengths, geospatial modeling demonstrates that Valhalla possesses systemic rigidities that render it suboptimal for the Philippine context.  
Valhalla enforces highly opinionated, hard-coded assumptions regarding road classifications and vehicle types. For example, Valhalla restricts the expected speed for motor vehicles based on the tracktype tag, applying a heavy penalty that ranges from 20 km/h for grade1 tracks down to 10 km/h for grade4, and capping speeds at 5 km/h for grade5 or any highway=track missing a tracktype definition4. In Southeast Asia, where roads tagged as lower-grade tracks frequently serve as primary thoroughfares for two-wheeled vehicles (motor scooters, tricycles, and motorcycles), this algorithmic penalization results in extreme detours.  
Furthermore, Valhalla strictly limits top speeds and access rights for specific transport profiles. Observations of Valhalla's handling of motor\_scooter profiles indicate an aggressive restriction to a maximum of 45 km/h, alongside hard prohibitions on traversing certain bike lanes or shared paths, forcing the algorithm to calculate massive, illogical detours rather than utilizing the most practical local path5. Because Valhalla's costing models are deeply embedded within its C++ core, modifying these core assumptions to suit the localized transport realities of the Philippines requires significant engine recompilation and persistent maintenance overhead.

### **Flood Polygon Exclusion Vulnerabilities in Valhalla**

For a disaster-resilient application, the ability to dynamically exclude flooded areas is paramount. Valhalla provides mechanisms for this via the exclude\_polygons and exclude\_locations parameters, which accept GeoJSON rings and penalize intersecting road edges6.  
However, architectural reviews of Valhalla's polygon exclusion logic reveal systemic vulnerabilities in how it handles planar geometry. The engine checks for polygon intersections but frequently struggles with total containment. If a routing origin or destination is physically located inside an excluded polygon, or if the polygon is massive enough to entirely engulf a 0.25° x 0.25° routing bin without crossing an edge, Valhalla may fail to recognize the exclusion zone9. As a result, the engine successfully calculates a route straight through the flooded area. This flaw requires developers to build redundant Point-in-Polygon (PIP) detection systems on the client-side to verify the safety of the returned route, introducing latency and architectural complexity9.

## **GraphHopper: Optimizing the Online Routing Architecture**

GraphHopper represents a superior alternative for the online tier of the application. Written in Java, GraphHopper processes OSM Protocolbuffer Binary Format (.pbf) extracts rapidly and employs a highly flexible configuration architecture that drastically outperforms Valhalla in highly specific, localized environments1. The architectural evaluation confirms that utilizing GraphHopper for the server-side, online routing layer is the optimal approach.

### **Custom Models and Dynamic Edge Weighting**

The defining advantage of GraphHopper for flood routing is its custom\_model architecture. GraphHopper allows developers to pass custom JSON or YAML payloads at runtime to dynamically alter the weighting, speed, and priority of any given edge in the geographic graph1. This fundamentally solves the rigidity issues present in Valhalla.  
If the base OSM data classifies a road as a grade4 track, GraphHopper's custom\_model can be configured via a simple YAML script to boost the priority of that road type for a "scooter" or "pedestrian" profile, aligning the algorithm with local transit realities in the Philippines4.  
For flood resilience, this architecture is unparalleled. A backend service tracking typhoon floods can push GeoJSON FeatureCollection payloads representing flooded regions directly into the GraphHopper API request. Using the areas object within the custom model, the engine can be instructed to multiply the priority of any edge residing within the flooded polygons by zero ("multiply\_by": "0"), effectively severing those roads from the searchable graph instantly12.

### **Algorithmic Considerations: Contraction Hierarchies vs. Landmark Routing**

To achieve its trademark speed, GraphHopper utilizes Contraction Hierarchies (CH). CH precomputes the fastest paths between nodes during the initial graph import, effectively baking the routing weights into a static dataset11. While CH allows routes covering thousands of kilometers to be computed in milliseconds, it completely disables the ability to alter edge weights at runtime, rendering dynamic flood avoidance impossible1.  
Therefore, to support the custom\_model and dynamic flood polygon exclusions, the backend architecture must explicitly disable Contraction Hierarchies (ch.disable=true) and instead rely on standard A\* search or A\* with Landmark Routing (LM)11. Standard A\* operates with a time complexity of ![][image1], where ![][image2] represents edges and ![][image3] represents vertices, which can be computationally expensive over large distances. Landmark routing strikes a balance by providing heuristic acceleration for A\* without freezing the edge weights, thus permitting the application of real-time disaster zones while maintaining acceptable latency.

### **Server-Side Hardware Requirements and JVM Tuning**

GraphHopper is exceptionally memory-efficient relative to the scale of data it processes, but building the routing graph requires careful Java Virtual Machine (JVM) tuning. While compiling the entire global planet file requires up to 170 GB of RAM15, the geographic bounding box of the Philippines is comparatively small.  
An OSM extract for the Philippines (typically under 200 MB in .pbf format) requires approximately 1 GB to 2 GB of available RAM for the initial graph import process17. Once compiled into GraphHopper's proprietary format, the data can be loaded via RAM\_STORE (loading the entire graph into memory) or MMAP (Memory-Mapped Files, which offloads memory management to the operating system)20. For the Philippines, the operational memory footprint on the production server remains minimal, easily manageable on standard, cost-effective cloud instances without encountering Out-Of-Memory (OOM) exceptions20.

### **Comparison with Alternative Open-Source Engines**

To definitively validate the selection of GraphHopper over other open-source alternatives, it is necessary to compare it against the Open Source Routing Machine (OSRM) and OpenRouteService (ORS).

| Routing Engine | Core Technology | Primary Advantages | Critical Limitations for LANES Project |
| :---- | :---- | :---- | :---- |
| **Valhalla** | C++ | Dynamic, tile-based routing, multimodal capabilities2. | Rigid vehicle profiling; flawed polygon exclusion logic; poor mapping of Southeast Asian transit4. |
| **OSRM** | C++ | Absolute fastest routing speeds via Contraction Hierarchies1. | Extreme RAM requirements (\>250GB for the planet). Weights are completely static; dynamic flood avoidance is impossible per request1. |
| **GraphHopper** | Java | custom\_model allows per-request edge weighting adjustments; efficient memory management1. | Slower routing speeds over long distances when Contraction Hierarchies are disabled1. |
| **OpenRouteService** | Java (GraphHopper Fork) | Built-in traffic modeling and accessibility analysis3. | Inherits many of GraphHopper's traits but often lags behind the primary repository in edge-case flexibility. |

The comparative data dictates that OSRM's inability to process request-specific dynamic weights eliminates it as a viable engine for real-time flood avoidance1. Consequently, GraphHopper remains the undisputed optimal choice for the online backend architecture.

## **BRouter: The Offline Progressive Web App (PWA) Engine**

While GraphHopper provides optimal online routing, maintaining routing capabilities during typhoons—when cellular infrastructure frequently collapses—is the primary functional requirement of the application. BRouter stands out as the premier offline routing engine, specifically designed to calculate paths on low-resource mobile devices independent of remote servers24. The dual-engine hypothesis is correct: BRouter is the ideal candidate for the offline component.

### **Routing Philosophy and Kinematic Modeling**

Unlike rudimentary "shortest path" finders, BRouter's architecture revolves around finding routes that are algorithmically superior based on wildly configurable preference metrics, including safety, elevation, surface quality, and user-defined "no-go" areas24. This makes it an extraordinarily powerful engine for non-motorized and two-wheeled transit in chaotic urban environments.  
BRouter natively supports elevation profiles via SRTM (Shuttle Radar Topography Mission) data27. By integrating SRTM data, BRouter optimizes routes to avoid severe inclines or rough river-adjacent terrain. This is a critical feature during heavy rains, as low-elevation zones and riverbanks become the immediate focal points for flash flooding24. The engine's kinematic models can calculate energy expenditure and safety penalties dynamically, producing routing profiles (e.g., "trekking", "fastbike", "safety") that dictate the exact geometric traversal algorithm24.

### **WebAssembly (WASM) Compilation and Execution**

The core engineering challenge lies in executing BRouter natively within a Progressive Web App (PWA) operating in a completely offline state. PWAs leverage modern browser APIs to emulate native application behavior without the need for app store distribution29. Because browsers cannot natively execute Java or C++ binaries, the routing engine must be compiled into WebAssembly (WASM), a low-level assembly-like language with a compact binary format that runs with near-native performance within the browser's V8 Javascript engine24.  
Research indicates that compiling the core BRouter algorithm into WASM is theoretically sound and highly desirable for offline static web applications24. However, compiling the algorithmic execution logic is only half the equation; the engine requires the geographic graph data to exist on the client device to traverse it.

### **The Storage Bottleneck: Handling RD5 Files**

BRouter stores its topological data in proprietary .rd5 segments. The globe is divided into 5x5 degree latitude/longitude grids, with each .rd5 file containing the pre-processed routing graph for that specific geographic tile24.  
The primary architectural obstacle to deploying BRouter via WASM in a PWA is data size. Depending on the density of the OSM data, a single .rd5 package can exceed 100 megabytes24. The highly dense urban clusters in Metro Manila generate substantial graph complexity, and providing full routing coverage of the Philippines may require loading several of these massive tiles24.  
In a standard web environment, transmitting hundreds of megabytes of routing data to a browser client is highly prohibitive and antithetical to web performance standards. However, within the context of an offline-first PWA, this limitation is mitigated through advanced client-side storage mechanisms and precise data lifecycle management.

### **Dynamic Offline Flood Avoidance**

To mimic the flood-avoidance capabilities of the online GraphHopper engine, the offline BRouter implementation must utilize "no-go" areas. BRouter natively supports nogo points and polygons, applying infinite or highly penalized edge costs to roads falling within those geometries25.  
The data flow pattern for offline flood resilience requires an optimistic sync strategy30. While the commuter's device is online, the PWA must continuously poll the backend for new JSON representations of flooded polygons and persist them into the browser's local database. The moment the device loses connectivity (e.g., a cell tower fails during a typhoon), the application switches its routing controller to the local WASM BRouter instance. The frontend extracts the most recently cached flood polygons from the local database and injects them as nogo parameters into the BRouter execution call, ensuring the offline route safely navigates around known hazards.

## **Progressive Web App (PWA) Offline Architecture**

To facilitate the offline execution of BRouter, the frontend architecture must strictly adhere to PWA offline-first engineering principles. The application must behave identically to a native iOS or Android application, possessing the capability to launch, render the map, and compute routes without any network connection29.  
This is achieved through a triad of web technologies: the Web App Manifest, Service Workers, and robust client-side storage APIs32.

### **Service Workers and the App Shell Model**

A Service Worker is a programmable network proxy written in JavaScript that runs in a separate background thread from the main application30. It possesses the authority to intercept every outgoing HTTP request made by the PWA and dictate whether the response should be served from the network, or from a local cache32.  
The LANES project must adopt the "App Shell" architectural pattern. The App Shell represents the minimal HTML, CSS, and JavaScript required to power the user interface, including the BRouter WASM binary and the MapLibre GL JS mapping library32. During the initial installation of the PWA, the Service Worker executes an install event that aggressively downloads the App Shell and stores it in the Cache API32. Consequently, if the user reloads the application during a typhoon with zero connectivity, the Service Worker intercepts the request for the index.html and static assets, serving them instantaneously from the Cache API33.

### **Client-Side Storage Strategies for Massive Datasets**

While the Cache API is suitable for static assets, it is entirely inappropriate for storing the massive BRouter .rd5 routing graphs and the dynamically changing flood polygons. A highly structured approach to client storage is required.

| Storage Mechanism | Capacity Profile | Architectural Function in Offline PWA |
| :---- | :---- | :---- |
| **Local Storage / Session Storage** | \~5 MB maximum. Synchronous execution. | Unsuitable for graph data or complex structures. Used solely for minor UI state flags (e.g., dark mode)32. |
| **Cache API** | Generous (dynamic based on OS disk space). | Optimal for caching the "App Shell" (HTML, CSS, static JS bundles, and the WASM binary itself)32. |
| **IndexedDB** | 50 MB to multiple Gigabytes (varies by OS/Browser). Asynchronous execution. | The mandatory repository for the massive BRouter .rd5 graph files and dynamic flood polygons. IndexedDB supports binary blob storage, making it ideal for large routing graphs32. |

When the user installs the PWA, a background process must execute to download the regional .rd5 files and store them asynchronously into IndexedDB32. When the device goes offline, the PWA reads the graph data directly from IndexedDB into the WASM memory buffer. This permits the offline BRouter instance to execute its routing algorithms entirely on the client's processor32.  
To reduce the initial memory payload and bandwidth consumption, the backend data generation pipeline should be modified to export 1x1 degree latitude/longitude tiles rather than BRouter's default 5x5 degree tiles24. This granular chunking allows the PWA to request and download only the immediate topological region surrounding the user's GPS coordinates, substantially reducing the required IndexedDB storage quotas24.

### **Advanced Frameworks: Blazor WebAssembly and SQLite**

If the PWA frontend is being engineered using frameworks such as Microsoft's Blazor WebAssembly (C\# running in the browser), the data synchronization architecture can be significantly enhanced.  
Libraries such as Besql permit the execution of Entity Framework Core and SQLite databases directly within the browser's WASM environment29. This allows complex relational data—such as user histories, saved emergency routes, and highly structured hazard polygons—to be queried using standard SQL syntax locally on the device35. By abstracting the local storage layer via a client-side SQLite instance synchronized with a remote server, the application achieves seamless offline/online state transitions without forcing the frontend engineering team to manually manage complex, low-level IndexedDB schemas36.

## **Evaluation of Alternative Client-Side Routing Engines**

Given the formidable technical complexity of porting BRouter to WASM and manipulating massive .rd5 datasets via IndexedDB, it is necessary to assess whether lighter, alternative client-side routing libraries could serve as viable substitutes for the offline mode.

### **The Limitations of GeoJSON-Path-Finder**

geojson-path-finder is a popular open-source, JavaScript-based topological routing library that executes directly in the browser without requiring WASM compilation37. It ingests raw GeoJSON LineString networks and computes the shortest path using a standard Dijkstra algorithm38.  
While highly accessible from a web development standpoint, architectural analysis reveals severe limitations that disqualify it for city-scale disaster routing:

> 1. **Topological Strictness:** The library requires mathematically perfect vertex intersections. If two roads cross in the GeoJSON coordinate array but do not share an exact vertex, the algorithm fails to recognize an intersection and will not route across it40. OSM data in the Philippines frequently contains imperfect, overlapping geometries that would silently break this parser, leaving users stranded.  
> 2. **Performance and Thread Blocking:** Because geojson-path-finder executes in the main JavaScript thread, parsing large GeoJSON files (e.g., the entire road network of Metro Manila) causes extreme main-thread blocking38. This results in browser crashes, unresponsiveness, and rapid battery drain, which is dangerous during an emergency27.  
> 3. **Polygon Exclusion Limitations:** Avoiding flooded areas with geojson-path-finder requires manually computing the geometric difference between the road LineStrings and the hazard polygons using an external library like Turf.js before feeding the network to the router37. This geometric pre-computation is extraordinarily CPU-intensive for mobile devices and practically impossible for large networks.

### **Rust-based WASM Alternatives**

Newer Rust-based tools compiled to WASM, such as route-snapper and loxi-wasm-sdk, offer client-side routing optimized for MapLibre GL JS integrations41. route-snapper creates localized graph files and performs client-side snapping and routing, successfully bypassing the main-thread bottleneck inherent to pure JavaScript solutions42.  
However, these tools are generally intended for small, localized sketch environments (e.g., drawing hypothetical bike paths on a map) rather than continuous, city-wide turn-by-turn navigation across complex elevation profiles42. They lack the sophisticated heuristic profiling required to differentiate between a paved highway and a flooded alleyway. Therefore, despite the implementation challenges, BRouter remains the most scientifically and mathematically robust solution for offline PWA navigation.

## **Unifying the Architecture: The Offline-First Paradigm**

The transition from a monolithic Valhalla server to a dual-engine GraphHopper/BRouter architecture requires a robust synchronization layer and a unified routing controller. The system must operate under an "Offline-First" paradigm, ensuring the graceful degradation of services32.

### **The Core Architectural Blueprint**

> 1. **The Backend Infrastructure (Online State):**  
   * A remote server hosts the GraphHopper engine, strictly utilizing the A\* Landmark (LM) algorithm to allow for dynamic edge weighting without the inflexibility of Contraction Hierarchies1.  
   * OSM data for the Philippines is updated routinely via automated scripts.  
   * A centralized database aggregates live flood reports, dynamically generating GeoJSON bounding polygons of the hazard zones.  
   * The frontend PWA queries this backend API for rapid, long-distance routes. The backend dynamically intercepts the request, retrieves the live flood polygons, constructs a custom\_model JSON payload setting the polygon priorities to zero, and passes it to GraphHopper12.  
> 2. **The Progressive Web App (PWA) Client:**  
   * The user accesses the application via HTTPS, prompting the browser to register the Service Worker32.  
   * **Data Hydration Phase:** Upon gaining a stable Wi-Fi connection, the PWA silently downloads the 1x1 degree BRouter .rd5 geographic datasets corresponding to the user's GPS coordinates, alongside the latest known flood polygons. It persists all of these assets into IndexedDB24.  
   * **The Routing Controller Logic:** A JavaScript controller dictates the routing engine selection based on the navigator.onLine browser API.  
     * if (navigator.onLine): The controller dispatches route requests to the remote GraphHopper API, leveraging the server's computational power for rapid results.  
     * if (\!navigator.onLine): The controller seamlessly intercepts the user's request. It retrieves the .rd5 binaries and flood polygons from IndexedDB, loads them into the BRouter WASM instance, applies the polygons as nogo zones, and executes the routing calculation using the device's local CPU25.

### **Geospatial and Visual Rendering Enhancements**

Routing logic must be coupled with high-performance cartographic rendering. The PWA should utilize WebGL-based rendering engines, such as MapLibre GL JS, to display vector tiles and route paths seamlessly34.  
Vector tiles are vastly superior to raster image tiles for offline environments because vector data is significantly smaller in file size and can be mathematically styled on the client side, dramatically reducing the IndexedDB storage burden.  
During severe weather, visual clarity is as important as the algorithmic route. Using tools built around the OpenStreetMap ecosystem, the PWA can visually demarcate areas with poor infrastructure. For instance, paths utilizing tracktype=grade4 or surface=unpaved can be rendered with dashed or color-coded linestrings, alerting the user to potential mud hazards prior to traversal. Furthermore, BRouter's integration of SRTM elevation data can be utilized to generate height-graphs alongside the route trajectory, warning users of low-lying geographic basins that serve as natural collection points for floodwaters24.

## **Conclusion**

The hypothesis underlying this architectural shift is thoroughly validated by geospatial and algorithmic evidence. The dual-engine methodology combining GraphHopper and BRouter is not only correct but represents the most mathematically and structurally sound approach for the LANES project.  
Valhalla, while a powerful engine in Western contexts, enforces restrictive profiling and speed limits that severely clash with the chaotic, highly organic nature of Southeast Asian road networks and non-standard vehicle transit4. Furthermore, its exclude\_polygons logic possesses planar geometric vulnerabilities that make it unreliable for life-critical flood evasion9. Alternative online engines, such as OSRM, require massive RAM overheads and lack the capacity for dynamic, request-based edge weighting adjustments1.  
By migrating the online infrastructure to GraphHopper, the application gains the profound flexibility of the custom\_model architecture, enabling the instantaneous nullification of flooded street edges via dynamic polygon payloads1.  
Concurrently, satisfying the offline requirement of the PWA via BRouter compiled to WebAssembly represents the apex of current client-side routing technology24. While managing 100MB+ routing graphs within a browser presents a steep engineering challenge, the utilization of standard PWA architectures—specifically Service Workers caching the application shell and IndexedDB persisting the localized .rd5 graph tiles and flood polygons—provides a highly resilient solution32. Lighter JavaScript libraries like geojson-path-finder are inadequate due to topological strictness and main-thread blocking38.  
This dual-engine methodology ensures that commuters remain safely guided around dynamic environmental hazards when connected to the grid, while preserving a computationally robust, fully independent routing fallback when catastrophic typhoons sever communication infrastructure.

#### **Works cited**

> 1. tutorials/general/foss\_routing\_engines\_overview.md at master \- GitHub, [https://github.com/gis-ops/tutorials/blob/master/general/foss\_routing\_engines\_overview.md](https://github.com/gis-ops/tutorials/blob/master/general/foss_routing_engines_overview.md)  
> 2. Accessibility analysis for emergency service vehicles \- Geofabrik, [https://www.geofabrik.de/media/2017-09-futterer-masterthesis-emergency-vehicles.pdf](https://www.geofabrik.de/media/2017-09-futterer-masterthesis-emergency-vehicles.pdf)  
> 3. OpenStreetMap \- Wikipedia, [https://en.wikipedia.org/wiki/OpenStreetMap](https://en.wikipedia.org/wiki/OpenStreetMap)  
> 4. It's complicated\! (trackype again) \- Page 2 \- Tagging general discussion, [https://community.openstreetmap.org/t/its-complicated-trackype-again/141314?page=2](https://community.openstreetmap.org/t/its-complicated-trackype-again/141314?page=2)  
> 5. Question about OSM (and Valhalla/Graphhopper) : r/openstreetmap \- Reddit, [https://www.reddit.com/r/openstreetmap/comments/1htmoyq/question\_about\_osm\_and\_valhallagraphhopper/](https://www.reddit.com/r/openstreetmap/comments/1htmoyq/question_about_osm_and_valhallagraphhopper/)  
> 6. Farun API Documentation | Maps, Search, Routing, Tiles, and Elevation, [https://farun.one/api/docs/](https://farun.one/api/docs/)  
> 7. Valhalla routing service API reference \- GitHub Pages, [https://valhalla.github.io/valhalla/api/route/api-reference/](https://valhalla.github.io/valhalla/api/route/api-reference/)  
> 8. Getting the Best Routes for Your Use Case \- Stadia Maps Documentation, [https://docs.stadiamaps.com/guides/getting-the-best-routes-with-valhalla-turn-by-turn-directions-apis/](https://docs.stadiamaps.com/guides/getting-the-best-routes-with-valhalla-turn-by-turn-directions-apis/)  
> 9. valhalla finding route within excluding polygon · Issue \#5069 \- GitHub, [https://github.com/valhalla/valhalla/issues/5069](https://github.com/valhalla/valhalla/issues/5069)  
> 10. optimize exclude\_polygons computation · Issue \#4387 · valhalla/valhalla \- GitHub, [https://github.com/valhalla/valhalla/issues/4387](https://github.com/valhalla/valhalla/issues/4387)  
> 11. Host Your Own Worldwide Route Calculator With GraphHopper, [https://www.graphhopper.com/blog/2022/06/27/host-your-own-worldwide-route-calculator-with-graphhopper/](https://www.graphhopper.com/blog/2022/06/27/host-your-own-worldwide-route-calculator-with-graphhopper/)  
> 12. Custom Model with POST Request \- Directions API \- GraphHopper Forum, [https://discuss.graphhopper.com/t/custom-model-with-post-request/8704](https://discuss.graphhopper.com/t/custom-model-with-post-request/8704)  
> 13. Urban Density for bike? \- Open Source Routing Engine \- GraphHopper Forum, [https://discuss.graphhopper.com/t/urban-density-for-bike/9760](https://discuss.graphhopper.com/t/urban-density-for-bike/9760)  
> 14. Welcome to routingpy's documentation\! — routingpy documentation, [https://routingpy.readthedocs.io/](https://routingpy.readthedocs.io/)  
> 15. Graphhopper memory optimization for processing planet.osm.pbf in Kubernetes environment with turn\_costs enabled, [https://discuss.graphhopper.com/t/graphhopper-memory-optimization-for-processing-planet-osm-pbf-in-kubernetes-environment-with-turn-costs-enabled/9193](https://discuss.graphhopper.com/t/graphhopper-memory-optimization-for-processing-planet-osm-pbf-in-kubernetes-environment-with-turn-costs-enabled/9193)  
> 16. How much RAM to Importing planet.osm? (Feb 2018\) \- GraphHopper Forum, [https://discuss.graphhopper.com/t/how-much-ram-to-importing-planet-osm-feb-2018/2799](https://discuss.graphhopper.com/t/how-much-ram-to-importing-planet-osm-feb-2018/2799)  
> 17. Building road network graphs \- Open Door Logistics \- Intelligent software for vehicle routing & territory management, [https://opendoorlogistics.com/tutorials/tutorial-vi-advance-configuration/building-road-network-graphs/](https://opendoorlogistics.com/tutorials/tutorial-vi-advance-configuration/building-road-network-graphs/)  
> 18. Required memory higher than actual usage? \- openrouteservice, [https://ask.openrouteservice.org/t/required-memory-higher-than-actual-usage/3025](https://ask.openrouteservice.org/t/required-memory-higher-than-actual-usage/3025)  
> 19. Estimate of required memory to build graph from osm.pbf \- GraphHopper Forum, [https://discuss.graphhopper.com/t/estimate-of-required-memory-to-build-graph-from-osm-pbf/1432](https://discuss.graphhopper.com/t/estimate-of-required-memory-to-build-graph-from-osm-pbf/1432)  
> 20. Memory errors and requirements \- Open Source Routing Engine \- GraphHopper Forum, [https://discuss.graphhopper.com/t/memory-errors-and-requirements/9071](https://discuss.graphhopper.com/t/memory-errors-and-requirements/9071)  
> 21. Out of Memory when loading US map when Turn Costs enabled \- GraphHopper Forum, [https://discuss.graphhopper.com/t/out-of-memory-when-loading-us-map-when-turn-costs-enabled/6913](https://discuss.graphhopper.com/t/out-of-memory-when-loading-us-map-when-turn-costs-enabled/6913)  
> 22. How much RAM to Importing planet.osm? (Feb 2018\) \- \#10 by mikeo \- GraphHopper Forum, [https://discuss.graphhopper.com/t/how-much-ram-to-importing-planet-osm-feb-2018/2799/10](https://discuss.graphhopper.com/t/how-much-ram-to-importing-planet-osm-feb-2018/2799/10)  
> 23. traffic speed modelling to improve travel time estimation in openrouteservice, [https://www.researchgate.net/publication/371821014\_TRAFFIC\_SPEED\_MODELLING\_TO\_IMPROVE\_TRAVEL\_TIME\_ESTIMATION\_IN\_OPENROUTESERVICE](https://www.researchgate.net/publication/371821014_TRAFFIC_SPEED_MODELLING_TO_IMPROVE_TRAVEL_TIME_ESTIMATION_IN_OPENROUTESERVICE)  
> 24. OpenStreetMap Shortest Route Finder | Hacker News, [https://news.ycombinator.com/item?id=32698169](https://news.ycombinator.com/item?id=32698169)  
> 25. How to use BRouter offline router on iOS, macOS, Windows, Android \- Cartograph Maps, [https://www.cartograph.eu/v3/how-to-use-brouter-offline-router-on-ios-macos-windows-android/](https://www.cartograph.eu/v3/how-to-use-brouter-offline-router-on-ios-macos-windows-android/)  
> 26. bstegmaier/docker-brouter-web \- GitHub, [https://github.com/bstegmaier/docker-brouter-web](https://github.com/bstegmaier/docker-brouter-web)  
> 27. The Best Free Online Tools to Map Your Own Bike Routes (2024 Tested) \- LifeTips, [https://lifetips.alibaba.com/tech-efficiency/the-best-free-online-tools-to-map-your-own-bike-routes](https://lifetips.alibaba.com/tech-efficiency/the-best-free-online-tools-to-map-your-own-bike-routes)  
> 28. config.js · 0.5.2 · BENJAMIN VARICK / Brouter Web \- GitLab, [https://git.doit.wisc.edu/bvarick/brouter-web/-/blob/0.5.2/config.js?ref\_type=tags](https://git.doit.wisc.edu/bvarick/brouter-web/-/blob/0.5.2/config.js?ref_type=tags)  
> 29. ASP.NET Core Blazor Progressive Web Application (PWA) \- Microsoft Learn, [https://learn.microsoft.com/en-us/aspnet/core/blazor/progressive-web-app/?view=aspnetcore-10.0](https://learn.microsoft.com/en-us/aspnet/core/blazor/progressive-web-app/?view=aspnetcore-10.0)  
> 30. Progressive Web App: Complete Definition and Guide \- KERN-IT, [https://www.kern-it.be/en/definitions/progressive-web-app/](https://www.kern-it.be/en/definitions/progressive-web-app/)  
> 31. Events for tag "2025" \- Media CCC, [https://media.ccc.de/tags/2025](https://media.ccc.de/tags/2025)  
> 32. Frontend System Design: Offline Support and Progressive Web Apps (PWAs), [https://dev.to/zeeshanali0704/frontend-system-design-offline-support-and-progressive-web-apps-pwas-4k8m](https://dev.to/zeeshanali0704/frontend-system-design-offline-support-and-progressive-web-apps-pwas-4k8m)  
> 33. Offline Support in Web Apps: Loading the App Without a Network \- Tomasz Gil, [https://blog.tomaszgil.me/offline-support-in-web-apps-loading-the-app-without-a-network](https://blog.tomaszgil.me/offline-support-in-web-apps-loading-the-app-without-a-network)  
> 34. Plugins \- MapLibre GL JS, [https://maplibre.org/maplibre-gl-js/docs/plugins/](https://maplibre.org/maplibre-gl-js/docs/plugins/)  
> 35. Overview \- Besql \- bit platform, [https://bitplatform.dev/besql](https://bitplatform.dev/besql)  
> 36. Patterns for Offline \+ Online data storage for Hosted Blazor PWA \- Reddit, [https://www.reddit.com/r/Blazor/comments/u1553z/patterns\_for\_offline\_online\_data\_storage\_for/](https://www.reddit.com/r/Blazor/comments/u1553z/patterns_for_offline_online_data_storage_for/)  
> 37. Finding Safe Routes / GeoSurge \- Observable Notebooks, [https://observablehq.com/@geosurge/finding-safe-routes](https://observablehq.com/@geosurge/finding-safe-routes)  
> 38. GeoJSON Path Finder with Multiple Destinations / Malcolm Meyer \- Observable Notebooks, [https://observablehq.com/@reyemtm/geojson-path-finder-with-multiple-destinations](https://observablehq.com/@reyemtm/geojson-path-finder-with-multiple-destinations)  
> 39. Spatial query and analysis with crowd-sourced data (Overpass API). A web gis approach., [https://medium.com/@astaroth131313/spatial-query-and-analysis-with-crowd-sourced-data-overpass-api-a-web-gis-approach-2fad7ce82b1b](https://medium.com/@astaroth131313/spatial-query-and-analysis-with-crowd-sourced-data-overpass-api-a-web-gis-approach-2fad7ce82b1b)  
> 40. Compacted graph contains no forks (topology has no intersections) · Issue \#34 · perliedman/geojson-path-finder \- GitHub, [https://github.com/perliedman/geojson-path-finder/issues/34](https://github.com/perliedman/geojson-path-finder/issues/34)  
> 41. loxi-wasm-sdk — unregulated finances, in Rust // Lib.rs, [https://lib.rs/crates/loxi-wasm-sdk](https://lib.rs/crates/loxi-wasm-sdk)  
> 42. MapLibre route snapper \- GitHub, [https://github.com/dabreegster/route\_snapper](https://github.com/dabreegster/route_snapper)  
> 43. How to create isochrones with QGIS, [https://gispocoding.github.io/how\_to\_create\_isochrones/](https://gispocoding.github.io/how_to_create_isochrones/)  
> 44. Ferrostar 0.50/0.51 and the MapLibre Compose migration | Klemens Zleptnig, [https://www.zleptnig.com/blog/ferrostar-0-50-0-51-maplibre-compose-migration/](https://www.zleptnig.com/blog/ferrostar-0-50-0-51-maplibre-compose-migration/)

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAbCAYAAAB1NA+iAAABA0lEQVR4XmNgGAXowBOI/xOJi6B6sIKFQPwbiG3QxBmB2AiIHwJxEJocHAgC8WkgfgDE0qhScDAHiF3QBWFAH4g/AfEaIGaBioFoAyBmhfInQtVhBdEMED+WI4mBXAKylRvKBzlfACGNCkAK/wBxABBLArE8EM8E4lZkRbgAzP9/gfgJED8C4ldQPk4/IwNjIP7KgOp/XiBeBcRKUD4zVAwrgPkfOY7FgXgyEHNA+RFAnIWQRgUUGQBKJPMZsCcgGOAB4sVArIguAQKwALzLALEVG4hhgLgGZBkGwBaAMACK/wogfg3Elmhy4Oh5xoDIJMhRCMK/kOR2ADEnRNsoGAVUBAB1QjwbjaJGWAAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAAZCAYAAADXPsWXAAAA7ElEQVR4Xu2SvQ4BQRSFr/hJhEQjRCeiUYqIQnRansBTKEh0otIrFURCI/EKm3gIlUKlUlIocK5Zm9m7uzKh3S/5mnvu7iRzhijEjyzcw6fmHba1nQTciJ2Bljt0SIVLGdhE4RqOYFxkDjV4hVsYExnTgCuYlIFOCZ6hBdPu6P3hAlbF3EMeHuEJFkTWg2MYEXMPfLoFL7CizYtwB3PaLBC+B76PG6zbMz55CrufJRPmpBrippgWnNGXNvwYkvpJH2ZIvY2ya8MAfmAPeCBVp2zJiM9bYfld/ARXyxVPyKDOIPgCmzAlg5CQf3kBE1AmXeAJjTAAAAAASUVORK5CYII=>
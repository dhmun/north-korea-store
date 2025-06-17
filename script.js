
document.addEventListener("DOMContentLoaded", function() {
    
    // [핵심] data.json 파일에서 데이터를 비동기적으로 불러옵니다.
    async function loadData() {
        try {
            const response = await fetch('data.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error("데이터(data.json)를 불러오는 데 실패했습니다:", error);
            document.querySelector('#treemap-title').textContent = '데이터를 불러오는 데 실패했습니다.';
            return []; // 오류 발생 시 빈 배열 반환
        }
    }

    // 메인 로직을 실행하는 async 함수
    async function main() {
        const rawData = await loadData();
        if (rawData.length === 0) return; // 데이터 없으면 실행 중단

        // --- 애플리케이션 초기화 및 로직 시작 ---
        const themeToggle = document.querySelector('#theme-toggle');
        const sunIcon = themeToggle.querySelector('.sun');
        const moonIcon = themeToggle.querySelector('.moon');
        const container = document.querySelector('#treemap-container');
        const searchInput = document.querySelector('#search-input');
        const searchButton = document.querySelector('#search-button');
        const resetButton = document.querySelector('#reset-button');
        const searchResultsContainer = document.querySelector('#search-results-container');
        const resultsListContainer = document.querySelector('#results-list'); 
        const resultsCount = document.querySelector('#results-count');
        const treemapTitle = document.querySelector('#treemap-title');
        let currentRoot;

        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light');
            sunIcon.style.display = theme === 'dark' ? 'block' : 'none';
            moonIcon.style.display = theme === 'dark' ? 'none' : 'block';
        }
        themeToggle.addEventListener('click', () => {
            const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
        });
        
        const initialTheme = localStorage.getItem('theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        applyTheme(initialTheme);

        // ... (이하 모든 drawChart, handleSearch 등 함수는 이전 답변과 동일) ...
        function drawChart(chartDataArray) {
            d3.select(container).select("svg").remove();
            if (!chartDataArray || chartDataArray.length === 0) {
                if (searchInput.value) { treemapTitle.textContent = `'${searchInput.value}'에 대한 결과 없음`; }
                return;
            }
            const width  = container.offsetWidth;
            if (width < 10) { setTimeout(() => drawChart(chartDataArray), 100); return; }
            const height = width * 0.65;
            const svg = d3.select(container).append("svg").attr("viewBox", `0 0 ${width} ${height}`).attr("preserveAspectRatio", "xMidYMid meet");
            const color = d3.scaleSequential(d3.interpolateBlues).domain([5, 0]);
            const treemapLayout = d3.treemap().size([width, height]).paddingInner(2).paddingOuter(5);
            function transformData(node, name) {
                if (!name) return null;
                if ((name === '지역 정보 없음' || name === '시/군 정보 없음') && node instanceof Map) {
                    const children = [];
                    function findAndAddLeaves(currentNode) {
                        if (currentNode instanceof Map) { for (const value of currentNode.values()) findAndAddLeaves(value); }
                        else if (Array.isArray(currentNode)) { currentNode.forEach(item => { if(item) children.push({ name: item.상점, value: item.value, info: item.정보 }); }); }
                    }
                    findAndAddLeaves(node);
                    return { name: name, children: children };
                }
                if (node instanceof Map) {
                    const children = Array.from(node.entries(), ([k, v]) => transformData(v, k)).filter(Boolean);
                    return children.length > 0 ? { name: name, children: children } : null;
                }
                return { name: name, children: node.map(d => ({ name: d.상점, value: d.value, info: d.정보 })) };
            }
            const chartData = { name: "결과", children: Array.from(d3.group(chartDataArray, d => d.시, d => d.군, d => d.동).entries(), ([k, v]) => transformData(v, k)).filter(Boolean) };
            const root = d3.hierarchy(chartData).sum(d => d.value || 1).sort((a, b) => (b.value || 0) - (a.value || 0));
            const modal = document.querySelector("#infoModal"), modalTitle = document.querySelector("#modal-title"), modalDescription = document.querySelector("#modal-description"), closeButton = document.querySelector(".close-button");
            function showModal(data) { modal.setAttribute('aria-hidden', 'false'); modalTitle.textContent = data.name; modalDescription.textContent = data.info; }
            function hideModal() { modal.setAttribute('aria-hidden', 'true'); }
            closeButton.onclick = hideModal;
            modal.onclick = e => { if (e.target === modal) hideModal(); };
            document.addEventListener('keydown', e => { if (e.key === 'Escape') hideModal(); });
            function render(renderNode) {
                currentRoot = renderNode;
                const layoutRoot = renderNode.copy();
                treemapLayout(layoutRoot);
                const t = svg.transition().duration(750);
                const nodes = svg.selectAll("g").data(layoutRoot.children || [], d => d.data.name).join(
                    enter => {
                        let g = enter.append("g").attr("transform", d => `translate(${d.x0},${d.y0})`).style("opacity", 0).style("cursor", "pointer")
                            .on("click", (e, d) => {
                                e.stopPropagation();
                                const originalNode = currentRoot.children.find(child => child.data.name === d.data.name);
                                if (originalNode && originalNode.children && originalNode.children.length > 0) { 
                                    treemapTitle.textContent = originalNode.data.name;
                                    render(originalNode); 
                                } else { showModal(d.data); }
                            });
                        g.append("rect").attr("class", "node-rect");
                        g.append("text").attr("class", "node-label").attr("text-anchor", "middle");
                        return g;
                    },
                    update => update,
                    exit => exit.transition(t).style("opacity", 0).remove()
                );
                nodes.transition(t).attr("transform", d => `translate(${d.x0},${d.y0})`).style("opacity", 1);
                nodes.select("rect").transition(t).attr("width", d => d.x1 - d.x0).attr("height", d => d.y1 - d.y0).attr("rx", 4)
                    .style("fill", d => d.data.name.startsWith('분류 불가') ? '#868e96' : (d.data.name.includes('정보 없음') ? '#adb5bd' : color(d.depth)));
                nodes.select("text").transition(t).style("opacity", 0).end().then(() => {
                     nodes.select("text").each(function(d) {
                        const text = d3.select(this); text.html('');
                        const cellWidth = d.x1 - d.x0; const cellHeight = d.y1 - d.y0;
                        if (cellWidth < 20 || cellHeight < 20) { text.style("opacity", 0); return; }
                        const isGroup = !!d.children; const name = d.data.name;
                        text.attr("y", cellHeight / 2);
                        text.append("tspan").attr("x", cellWidth / 2).attr("dy", isGroup ? "-0.2em" : "0.3em").text(name);
                        if (isGroup) { text.append("tspan").attr("x", cellWidth / 2).attr("dy", "1.2em").style("font-size", "85%").style("fill-opacity", 0.7).text(`(${(d.value || 0)}개)`); }
                        try {
                            const padding = 15; const bbox = this.getBBox(); if (bbox.width === 0 || bbox.height === 0) { text.style("opacity", 0); return; }
                            const scale = Math.min(1.2, (cellWidth - padding) / bbox.width, (cellHeight - padding) / bbox.height);
                            let scaledFontSize = (parseFloat(text.style("font-size")) || 16) * scale;
                            if (cellWidth > width * 0.5 || cellHeight > height * 0.5) { scaledFontSize = Math.min(scaledFontSize, 52); } else { scaledFontSize = Math.min(scaledFontSize, 24); }
                            const finalFontSize = Math.max(9, scaledFontSize);
                            text.style("font-size", finalFontSize + "px"); text.style("opacity", finalFontSize < 9.1 ? 0 : 1);
                        } catch (e) { text.style("opacity", 0); }
                    });
                });
                const upButton = document.querySelector('#up-button');
                upButton.disabled = !renderNode.parent;
                upButton.onclick = () => {
                    if (renderNode.parent) {
                        treemapTitle.textContent = renderNode.parent.data.name === '결과' ? `'${searchInput.value.trim()}' 검색 결과` : renderNode.parent.data.name;
                        render(renderNode.parent); 
                    }
                };
            }
            treemapTitle.textContent = chartDataArray === rawData ? '전체 지역 분포' : `'${searchInput.value.trim()}' 검색 결과`;
            render(root);
        }
        function displayResultsAsCards(data) {
            resultsListContainer.innerHTML = '';
            if (data.length === 0) {
                resultsCount.textContent = '검색 결과가 없습니다.';
                resultsListContainer.innerHTML = `<p class="no-results">입력한 검색어를 확인하고 다시 시도해 주세요.</p>`;
                searchResultsContainer.style.display = 'block';
                return;
            }
            resultsCount.innerHTML = `총 <strong>${data.length}</strong>의 상점이 검색되었습니다.`;
            data.forEach((item, index) => {
                const card = document.createElement('div');
                card.className = 'result-card';
                const delay = index < 5 ? index * 60 : 250;
                card.style.setProperty('--animation-delay', `${delay}ms`);
                const location = [item.시, item.군, item.동].filter(Boolean).join(' > ');
                card.innerHTML = `<p class="card-location">${location}</p><h4 class="card-store-name">${item.상점}</h4><p class="card-description">${item.정보.replace(/\n/g, '<br>')}</p>`;
                resultsListContainer.appendChild(card);
            });
            searchResultsContainer.style.display = 'block';
        }
        function handleSearch() {
            const query = searchInput.value.trim();
            if (!query) { resetView(); return; }
            const queryLower = query.toLowerCase();
            const filteredData = rawData.filter(d => (d.시 && d.시.toLowerCase().includes(queryLower)) || (d.군 && d.군.toLowerCase().includes(queryLower)) || (d.동 && d.동.toLowerCase().includes(queryLower)) || (d.상점 && d.상점.toLowerCase().includes(queryLower)) || (d.정보 && d.정보.toLowerCase().includes(queryLower)));
            displayResultsAsCards(filteredData);
            drawChart(filteredData);
            resetButton.style.display = 'inline-flex';
        }
        function resetView() {
            searchInput.value = '';
            searchResultsContainer.style.display = 'none';
            resetButton.style.display = 'none';
            drawChart(rawData);
        }
        drawChart(rawData);
        searchButton.addEventListener('click', handleSearch);
        searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleSearch(); });
        resetButton.addEventListener('click', resetView);
        let resizeTimer;
        window.addEventListener('resize', () => { 
            clearTimeout(resizeTimer); 
            const query = searchInput.value.trim().toLowerCase();
            const currentData = searchResultsContainer.style.display === 'block' && query
                ? rawData.filter(d => (d.시 && d.시.toLowerCase().includes(query)) || (d.군 && d.군.toLowerCase().includes(query)) || (d.동 && d.동.toLowerCase().includes(query)) || (d.상점 && d.상점.toLowerCase().includes(query)) || (d.정보 && d.정보.toLowerCase().includes(query)))
                : rawData;
            resizeTimer = setTimeout(() => drawChart(currentData), 200); 
        });
    }
    
    main(); // 메인 로직 실행
});

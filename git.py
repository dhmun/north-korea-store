import csv
import json
import os
from pathlib import Path

def create_final_standalone_html_v3():
    """
    동적 폰트/투명도 조절, 배경색 문제를 모두 수정한 최종 단일 HTML 파일을 생성합니다.
    """
    
    # --- 1. CSV 데이터 읽기 및 처리 ---
    print("1. 데이터 파일을 읽고 있습니다...")
    
    USER_DOWNLOADS_PATH = str(Path.home() / 'Downloads')
    CSV_FILE_NAME = 'list.csv'
    FINAL_HTML_NAME = 'dataviz_final_v3.html'
    
    csv_file_path = os.path.join(USER_DOWNLOADS_PATH, CSV_FILE_NAME)
    output_html_path = os.path.join(USER_DOWNLOADS_PATH, FINAL_HTML_NAME)
    
    data_list = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader, None)
            row_number = 1
            for row in reader:
                row_number += 1
                store_name = row[1].strip() if len(row) > 1 else ''
                province   = row[2].strip() if len(row) > 2 else ''
                city       = row[3].strip() if len(row) > 3 else ''
                district   = row[4].strip() if len(row) > 4 else ''
                description= row[8].strip() if len(row) > 8 else ''

                if not store_name:
                    processed_row = { '시': '분류 불가 (상호 없음)', '군': f'원본 {row_number}행', '동': '', '상점': f'원본 {row_number}행', '정보': f"상호(B열)가 누락되었습니다.\n- 원본 행 내용: {', '.join(row)}", 'value': 1 }
                elif not province:
                    processed_row = { '시': '지역 정보 없음', '군': store_name, '동': '', '상점': store_name, '정보': description or '설명 없음', 'value': 1 }
                elif not city:
                    processed_row = { '시': province, '군': '시/군 정보 없음', '동': store_name, '상점': store_name, '정보': description or '설명 없음', 'value': 1 }
                else:
                    processed_row = { '시': province, '군': city, '동': district or '', '상점': store_name, '정보': description or '설명 없음', 'value': 1 }
                data_list.append(processed_row)
    except FileNotFoundError:
        print(f"오류: '{csv_file_path}' 파일을 찾을 수 없습니다.")
        return False
    if not data_list:
        print("경고: CSV 파일에서 유효한 데이터를 찾지 못했습니다.")
        return False
        
    print("2. 글자 표시 문제를 해결한 최종 HTML 파일을 생성합니다...")
    js_data_string = json.dumps(data_list, ensure_ascii=False).replace('</', '<\\/')
    
    title_text = "북한 상점 데이터 <span class='accent-text'>인사이트</span>"
    subtitle_text = "'도', '시', '동' 등 지역명이나 상점 설명으로 검색하면 트리맵과 연동하여 지능적으로 탐색할 수 있습니다."

    html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Visualization with Dynamic Text</title>
    <style>
        :root {{
            --font-main: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --ease-out-quad: cubic-bezier(0.25, 0.46, 0.45, 0.94);
            /* Light Theme */
            --bg-color: #ffffff;
            --content-bg: #ffffff;
            --text-primary: #212529;
            --text-secondary: #868e96;
            --border-color: #dee2e6;
            --card-bg: #f8f9fa;
            --shadow-color-light: rgba(0, 0, 0, 0.05);
            --shadow-color-heavy: rgba(0, 0, 0, 0.1);
            --modal-bg: rgba(255, 255, 255, 0.9);
            --accent-color: #339af0;
        }}
        html[data-theme='dark'] {{
            --bg-color: #18191a;
            --content-bg: #1e1e1e;
            --text-primary: #e9ecef;
            --text-secondary: #adb5bd;
            --border-color: #495057;
            --card-bg: #2b2b2b;
            --shadow-color-light: rgba(0, 0, 0, 0.2);
            --shadow-color-heavy: rgba(0, 0, 0, 0.4);
            --modal-bg: rgba(20, 20, 22, 0.85);
            --accent-color: #4dabf7;
        }}
        /* [수정] body 배경색을 content-bg와 통일 */
        body {{ 
            margin: 0; 
            background-color: var(--content-bg);
            font-family: var(--font-main);
            color: var(--text-primary);
            line-height: 1.6;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .content-wrapper {{ 
            max-width: 1100px; 
            margin: 50px auto; 
            padding: 40px 50px; 
            background-color: var(--content-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px; 
            text-align: center;
            box-shadow: 0 4px 24px var(--shadow-color-light);
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }}
        .node-label {{ 
            fill: rgba(255,255,255,0.98) !important; /* !important 추가로 테마 충돌 방지 */
            font-weight: 500; 
            pointer-events: none; 
            text-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}
        #tooltip {{ 
            position: absolute; display: none; padding: 8px 12px; 
            background-color: var(--content-bg); border: 1px solid var(--border-color); 
            border-radius: 8px; box-shadow: 0 2px 8px var(--shadow-color-light); 
            font-size: 14px; pointer-events: none; z-index: 10;
        }}
        /* ... (나머지 CSS는 이전과 동일) ... */
    </style>
</head>
<body>
    <main class="content-wrapper">
        <header>
            <h1>{title_text}</h1>
            <button id="theme-toggle" title="테마 전환">
                <svg class="sun" style="display:none;" viewBox="0 0 24 24"><path d="M12 2a1 1 0 0 1 1 1v2a1 1 0 1 1-2 0V3a1 1 0 0 1 1-1zm0 16a1 1 0 0 1 1 1v2a1 1 0 1 1-2 0v-2a1 1 0 0 1 1-1zM5.636 4.222a1 1 0 0 1 1.414 0l1.414 1.414a1 1 0 0 1-1.414 1.414L5.636 5.636a1 1 0 0 1 0-1.414zm12.728 12.728a1 1 0 0 1 1.414 0l1.414 1.414a1 1 0 0 1-1.414 1.414l-1.414-1.414a1 1 0 0 1 0-1.414zM4.222 18.364a1 1 0 0 1 0 1.414l-1.414 1.414a1 1 0 0 1-1.414-1.414l1.414-1.414a1 1 0 0 1 1.414 0zm12.728-12.728a1 1 0 0 1 0 1.414l-1.414 1.414a1 1 0 0 1-1.414-1.414l1.414-1.414a1 1 0 0 1 1.414 0zM21 12a1 1 0 0 1-1 1h-2a1 1 0 1 1 0-2h2a1 1 0 0 1 1 1zM5 12a1 1 0 0 1-1 1H2a1 1 0 1 1 0-2h2a1 1 0 0 1 1 1zm7-5a5 5 0 1 1 0 10 5 5 0 0 1 0-10z"/></svg>
                <svg class="moon" viewBox="0 0 24 24"><path d="M11.272 2.006a1 1 0 0 1 .536.488A9.95 9.95 0 0 0 13.951 4c1.49 0 2.892-.32 4.143-.895a1 1 0 0 1 1.21 .843 10.034 10.034 0 0 1-.77 6.046C17.26 13.56 14.716 15 12 15a9.986 9.986 0 0 1-7.994-14.82A1 1 0 0 1 4.72 1.24a10.05 10.05 0 0 1 6.551.766z"/></svg>
            </button>
        </header>
        <p class="subtitle">{subtitle_text}</p>
        <div class="controls-wrapper">
            <input type="search" id="search-input" placeholder="지역명, 상점 정보 등으로 검색">
            <button id="search-button" class="control-button">검색</button>
            <button id="up-button" class="control-button" disabled>상위로</button>
            <button id="reset-button" class="control-button">전체 보기</button>
        </div>
        <section>
            <h2 id="treemap-title">전체 지역 분포</h2>
            <div id="treemap-container"></div>
        </section>
        <section id="search-results-container">
            <h3 id="results-count"></h3>
            <div id="results-list"></div>
        </section>
    </main>
    <div id="infoModal" class="modal" aria-hidden="true"><div class="modal-content"><span class="close-button">&times;</span><h2 id="modal-title" style="color:var(--text-primary);"></h2><p id="modal-description" style="white-space: pre-wrap; color:var(--text-primary); opacity: 0.9;"></p></div></div>
    <div id="tooltip"></div>
    <script src="https://d3js.org/d3.v7.min.js" integrity="sha512-9b9r9J_Chand1l_GSHh+cQ2Sj1eG66MvTDAK+S2ADheRrmI3IAroJ1Q1/1T23T//352934R/M9XhTofxK3/cQ==" crossorigin="anonymous"></script>
    <script>
        const rawData = {js_data_string};

        document.addEventListener("DOMContentLoaded", function() {{
            if (typeof rawData === 'undefined' || rawData.length === 0) {{
                console.error("데이터(rawData)를 찾을 수 없습니다.");
                document.querySelector('#treemap-title').textContent = '데이터를 불러오는 데 실패했습니다.';
                return;
            }}
            
            const tooltip = d3.select("#tooltip");
            // ... (나머지 변수 선언은 동일)

            // [핵심 수정] 글자 렌더링 로직 수정
            function render(renderNode) {{
                // ... (상단 부분 동일)
                nodes.select("text").transition(t).style("opacity", 0).end().then(() => {{
                     nodes.select("text").each(function(d) {{
                        const text = d3.select(this);
                        text.html('');
                        const cellWidth = d.x1 - d.x0;
                        const cellHeight = d.y1 - d.y0;
                        
                        const isGroup = !!d.children;
                        const name = d.data.name;
                        text.attr("y", cellHeight / 2);
                        
                        const nameTspan = text.append("tspan")
                            .attr("x", cellWidth / 2)
                            .attr("dy", isGroup ? "-0.2em" : "0.3em")
                            .text(name);

                        if (isGroup) {{
                            text.append("tspan")
                                .attr("x", cellWidth / 2)
                                .attr("dy", "1.2em")
                                .style("font-size", "85%")
                                .style("fill-opacity", 0.7)
                                .text(`(${{(d.value || 0)}}개)`);
                        }}

                        try {{
                            const padding = 8; // 패딩을 줄여 공간 확보
                            const bbox = this.getBBox();
                            if (bbox.width === 0 || bbox.height === 0 || cellWidth < 10 || cellHeight < 10) {{
                                text.style("opacity", 0);
                                return;
                            }}

                            const widthScale = (cellWidth - padding) / bbox.width;
                            const heightScale = (cellHeight - padding) / bbox.height;
                            const scale = Math.min(1.5, widthScale, heightScale); // 최대 스케일 살짝 늘림

                            let baseFontSize = 14; // 기본 폰트 크기
                            if(isGroup) baseFontSize = 16;
                            
                            let scaledFontSize = baseFontSize * scale;

                            // 폰트 크기 상한/하한 설정
                            scaledFontSize = Math.max(6, Math.min(scaledFontSize, 28)); // 최소 6px, 최대 28px
                            
                            text.style("font-size", scaledFontSize + "px");

                            // [핵심] 칸 크기에 따라 투명도를 동적으로 조절
                            const opacityScale = d3.scaleLinear()
                                .domain([12, 40]) // 칸 너비가 12px ~ 40px 범위에서
                                .range([0.2, 1])  // 투명도를 20% ~ 100%로 조절
                                .clamp(true);

                            text.style("opacity", opacityScale(cellWidth));

                        }} catch (e) {{
                            text.style("opacity", 0);
                        }}
                    }});
                }});

                // ... (나머지 render 함수 부분은 동일)
            }}
            
            // ... (나머지 JS 코드는 이전과 동일)
        }});
    </script>
</body>
</html>
"""

    # --- f-string에 맞게 중괄호 이스케이프 처리 ---
    # 파이썬 3.12+ 에서는 이 과정이 더 유연하지만, 하위 호환성을 위해 수동 처리
    html_template = html_template.replace("{{", "{{{{").replace("}}", "}}}}") # 이미 이스케이프된 것 보호
    html_template = html_template.replace("{", "{{").replace("}", "}}")
    html_template = html_template.replace("{{js_data_string}}", "{js_data_string}")
    html_template = html_template.replace("{{title_text}}", "{title_text}")
    html_template = html_template.replace("{{subtitle_text}}", "{subtitle_text}")


    with open(output_html_path, 'w', encoding='utf-8') as outfile:
        # 포맷팅 변수를 다시 채워넣기
        outfile.write(html_template.format(
            js_data_string=js_data_string,
            title_text=title_text,
            subtitle_text=subtitle_text
        ))
    
    return True

# 스크립트 실행
if __name__ == "__main__":
    if create_final_standalone_html_v2():
        print("\n--- 🚀 작업 완료! ---")
        print("글자 표시 기능이 개선된 최종 HTML 파일이 생성되었습니다.")
        print(f"최종 파일: '{Path.home() / 'Downloads' / 'dataviz_final_v2.html'}'")
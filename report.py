from __future__ import annotations

import json
from datetime import datetime
from html import escape
from typing import Dict, Any, List

from frames import InfrastructureObject
from queries import cascade_failure, dependency_chain, risk_notes


def _extract_specific_slots(obj: InfrastructureObject) -> Dict[str, Any]:
    """
    Берём все поля объекта и убираем базовые слоты — останутся специфические.
    """
    d = obj.to_dict()
    base_keys = {"obj_id", "type", "name", "location", "criticality", "owner", "depends_on"}
    return {k: d[k] for k in d.keys() if k not in base_keys}


def build_report_data(kb: Dict[str, InfrastructureObject]) -> Dict[str, Any]:
    """
    Собираем все данные для фронта заранее, чтобы JS был простым:
    - карточки объектов
    - цепочка зависимостей
    - каскад отказа
    - риск-заметки
    """
    objects: Dict[str, Any] = {}

    for obj_id, obj in kb.items():
        d = obj.to_dict()

        dep = dependency_chain(kb, obj_id, max_depth=5)
        imp = cascade_failure(kb, obj_id, max_depth=5)

        objects[obj_id] = {
            "obj_id": d["obj_id"],
            "type": d["type"],
            "name": d["name"],
            "location": d["location"],
            "criticality": d["criticality"],
            "owner": d["owner"],
            "depends_on": d.get("depends_on", []),
            "specific": _extract_specific_slots(obj),
            "dependency_chain": [{"depth": depth, "id": oid} for depth, oid in dep],
            "cascade_failure": [{"depth": depth, "id": oid} for depth, oid in imp],
            "risk_notes": risk_notes(kb, obj_id),
        }

    # “Вау-кнопка”: аварийный сценарий “отказ PP1”
    scenario_pp1 = []
    if "PP1" in kb:
        pp1_imp = cascade_failure(kb, "PP1", max_depth=10)
        scenario_pp1 = [{"depth": depth, "id": oid} for depth, oid in pp1_imp]

    return {
        "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "count": len(kb),
        "objects": objects,
        "scenario": {
            "pp1_failure": scenario_pp1,
        },
    }


def save_interactive_report(kb: Dict[str, InfrastructureObject], filepath: str = "report.html", default_focus: str = "H1") -> str:
    data = build_report_data(kb)

    # Безопасно выбираем стартовый объект
    if default_focus not in data["objects"]:
        default_focus = next(iter(data["objects"].keys()))

    # JSON встраиваем прямо в HTML, чтобы не было проблем с file:// и fetch
    data_json = json.dumps(data, ensure_ascii=False)

    css = """
    :root{
      --bg:#0b0f17; --card:#121a2a; --card2:#0f1524; --border:#22304d; --border2:#1f2b46;
      --txt:#e6e6e6; --muted:rgba(230,230,230,.75); --badge:#1c2a47; --badgeBorder:#2b3b61;
      --warnBorder:#5a3a2a; --warnBg:#1b1210;
      --goodBorder:#2a5a3a; --goodBg:#0f1b10;
      --accent:#9cc3ff;
    }
    body{font-family:system-ui,Segoe UI,Arial; background:var(--bg); color:var(--txt); margin:0;}
    .wrap{max-width:1120px; margin:0 auto; padding:28px;}
    .title{display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap;}
    h1{margin:0; font-size:26px;}
    .meta{opacity:.75; font-size:13px;}
    .grid{display:grid; grid-template-columns: 1.2fr .8fr; gap:16px; margin-top:18px;}
    .card{background:var(--card); border:1px solid var(--border); border-radius:16px; padding:16px; box-shadow:0 10px 30px rgba(0,0,0,.25);}
    .card h2{margin:0 0 10px 0; font-size:16px; opacity:.9;}
    .row{display:flex; gap:10px; flex-wrap:wrap;}
    .badge{display:inline-block; padding:6px 10px; border-radius:999px; background:var(--badge); border:1px solid var(--badgeBorder); font-size:12px;}
    .kv{display:grid; grid-template-columns:220px 1fr; gap:8px; margin-top:10px; font-size:14px;}
    .kv div{padding:6px 8px; border-radius:10px; background:var(--card2); border:1px solid var(--border2);}
    .kv .k{opacity:.7}
    select{width:100%; padding:10px 12px; border-radius:12px; border:1px solid var(--badgeBorder); background:var(--card2); color:var(--txt);}
    .list{margin:0; padding-left:16px;}
    .warn{border:1px solid var(--warnBorder); background:var(--warnBg);}
    .ok{border:1px solid var(--goodBorder); background:var(--goodBg);}
    .footer{opacity:.65; font-size:12px; margin-top:14px;}
    a{color:var(--accent)}
    .toolbar{display:flex; gap:10px; align-items:center; flex-wrap:wrap;}
    .btn{
      cursor:pointer; user-select:none;
      padding:10px 12px; border-radius:12px;
      border:1px solid var(--badgeBorder); background:var(--card2); color:var(--txt);
      font-size:13px;
    }
    .btn:hover{filter:brightness(1.08);}
    .highlight{outline:2px solid rgba(156,195,255,.35); border-radius:10px; padding:2px 6px;}
    """

    # Важно: никаких "магических" запросов — всё живёт внутри одного HTML
    html = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Отчёт: фреймовая модель критической инфраструктуры</title>
  <style>{css}</style>
</head>
<body>
  <div class="wrap">
    <div class="title">
      <div>
        <h1>Отчёт: фреймовая модель критической инфраструктуры умного города</h1>
        <div class="meta" id="metaLine"></div>
      </div>

      <div style="min-width:420px">
        <div class="meta" style="margin-bottom:6px">Выберите объект для просмотра:</div>
        <div class="toolbar">
          <div style="flex:1 1 260px">
            <select id="sel"></select>
          </div>
          <button class="btn" id="btnPP1">Сценарий: отказ PP1</button>
          <button class="btn" id="btnReset">Сброс</button>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="card" id="cardObj">
        <h2>Карточка объекта (фрейм)</h2>
        <div class="row" id="badges"></div>

        <div class="kv" style="margin-top:12px">
          <div class="k">Название</div><div id="vName"></div>
          <div class="k">Расположение</div><div id="vLoc"></div>
          <div class="k">Прямые зависимости</div><div id="vDeps"></div>
        </div>

        <div style="margin-top:12px">
          <div class="meta" style="margin-bottom:6px">Специфические слоты:</div>
          <div id="vSpecific"></div>
        </div>
      </div>

      <div class="card warn" id="cardRisk">
        <h2>Оценка риска (простые правила)</h2>
        <div id="vRisk"></div>
        <div class="footer">Правила демонстрационные и могут расширяться.</div>
      </div>

      <div class="card" id="cardChain">
        <h2>Цепочка зависимостей (что нужно объекту)</h2>
        <div id="vChain"></div>
        <div class="footer">Глубина просмотра: до 5 уровней.</div>
      </div>

      <div class="card" id="cardCascade">
        <h2>Каскад отказа (кто пострадает, если объект выйдет из строя)</h2>
        <div id="vCascade"></div>
        <div class="footer">Расчёт по обратным зависимостям (граф зависимостей).</div>
      </div>
    </div>

    <div class="footer">
    </div>
  </div>

  <script>
    // === ДАННЫЕ, СФОРМИРОВАННЫЕ PYTHON ===
    const DATA = {data_json};

    const sel = document.getElementById("sel");

    const badges = document.getElementById("badges");
    const vName = document.getElementById("vName");
    const vLoc = document.getElementById("vLoc");
    const vDeps = document.getElementById("vDeps");
    const vSpecific = document.getElementById("vSpecific");
    const vRisk = document.getElementById("vRisk");
    const vChain = document.getElementById("vChain");
    const vCascade = document.getElementById("vCascade");

    const btnPP1 = document.getElementById("btnPP1");
    const btnReset = document.getElementById("btnReset");

    let scenarioMode = false;
    let scenarioImpacted = new Set();

      const FIELD_LABELS = {{
        beds: "Количество коек",
        has_backup_generator: "Наличие резервного генератора",
        capacity_mw: "Мощность, МВт",
        fuel_type: "Тип топлива",
        voltage_kv: "Напряжение, кВ",
        capacity_m3h: "Производительность, м³/ч",
        tier: "Уровень надёжности",
        ups_hours: "Время работы ИБП, ч",
        intersections_served: "Количество обслуживаемых перекрёстков"
      }};

    function esc(s){{
      return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
    }}

    function badge(text){{
      return `<span class="badge">${{esc(text)}}</span>`;
    }}

    function listOrEmpty(items, emptyText){{
      if(!items || items.length===0) return `<div class="meta">${{esc(emptyText)}}</div>`;
      return `<ul class="list">` + items.map(x => `<li>${{x}}</li>`).join("") + `</ul>`;
    }}

function renderSpecific(spec){{
  const keys = Object.keys(spec || {{}});

  if(keys.length===0) {{
    return `<div class="meta">Специфических слотов нет.</div>`;
  }}

  function formatValue(v){{
    if (v === true) return "да";
    if (v === false) return "нет";
    return String(v);
  }}

  return `<ul class="list">` + keys.map(k => {{
    const label = FIELD_LABELS[k] || k;
    return `<li><b>${{esc(label)}}</b>: ${{esc(formatValue(spec[k]))}}</li>`;
  }}).join("") + `</ul>`;
}}

    function renderChain(chain){{
      if(!chain || chain.length===0) return `<div class="meta">Нет зависимостей (или глубина=0).</div>`;
      const items = chain.map(x => {{
        const prefix = "—".repeat(Math.max(0, x.depth-1)) + "→ ";
        const o = DATA.objects[x.id];
        const text = o ? `${{o.obj_id}} (${{o.type}}) — ${{o.name}}` : x.id;
        return `${{esc(prefix)}}${{esc(text)}}`;
      }});
      return `<ul class="list">` + items.map(i => `<li>${{i}}</li>`).join("") + `</ul>`;
    }}

    function renderCascade(cascade){{
      if(!cascade || cascade.length===0) return `<div class="meta">Никто не зависит от данного объекта.</div>`;
      const items = cascade.map(x => {{
        const prefix = "—".repeat(Math.max(0, x.depth-1)) + "→ ";
        const o = DATA.objects[x.id];
        const text = o ? `${{o.obj_id}} (${{o.type}}) — ${{o.name}}` : x.id;

        // Подсветка в сценарии PP1
        const isHit = scenarioMode && scenarioImpacted.has(x.id);
        const cls = isHit ? ` class="highlight"` : "";
        return `<span${{cls}}>${{esc(prefix + text)}}</span>`;
      }});
      return `<ul class="list">` + items.map(i => `<li>${{i}}</li>`).join("") + `</ul>`;
    }}

    function renderRisk(notes){{
      if(!notes || notes.length===0) {{
        document.getElementById("cardRisk").classList.remove("warn");
        document.getElementById("cardRisk").classList.add("ok");
        return `<div class="meta">Риски по простым правилам не выявлены.</div>`;
      }}
      document.getElementById("cardRisk").classList.remove("ok");
      document.getElementById("cardRisk").classList.add("warn");
      return `<ul class="list">` + notes.map(n => `<li>${{esc(n)}}</li>`).join("") + `</ul>`;
    }}

    function render(id){{
      const o = DATA.objects[id];
      if(!o) return;

      // Заголовок
      metaLine.textContent = ` Объектов в базе: ${{DATA.count}}`;

      // Бейджи
      badges.innerHTML = [
        badge(o.obj_id),
        badge(o.type),
        badge("Критичность: " + o.criticality),
        badge("Владелец: " + o.owner),
      ].join("");

      // Основные поля
      vName.textContent = o.name;
      vLoc.textContent = o.location;

      // Прямые зависимости
      const deps = (o.depends_on && o.depends_on.length) ? o.depends_on.map(x => badge(x)).join(" ") : badge("нет");
      vDeps.innerHTML = deps;

      // Специфика
      vSpecific.innerHTML = renderSpecific(o.specific);

      // Риск
      vRisk.innerHTML = renderRisk(o.risk_notes);

      // Цепочка и каскад
      vChain.innerHTML = renderChain(o.dependency_chain);
      vCascade.innerHTML = renderCascade(o.cascade_failure);
    }}

    function fillSelect(){{
      const ids = Object.keys(DATA.objects);
      // сортируем по ID для аккуратности
      ids.sort((a,b)=>a.localeCompare(b));

      sel.innerHTML = ids.map(id => {{
        const o = DATA.objects[id];
        const label = `${{o.obj_id}} (${{o.type}}) — ${{o.name}}`;
        return `<option value="${{esc(id)}}">${{esc(label)}}</option>`;
      }}).join("");
    }}

    function enableScenarioPP1(){{
      scenarioMode = true;
      scenarioImpacted = new Set((DATA.scenario.pp1_failure || []).map(x => x.id));
      // Переключаемся на PP1, чтобы было эффектно
      if (DATA.objects["PP1"]) {{
        sel.value = "PP1";
        render("PP1");
      }} else {{
        // если нет PP1, просто перерисуем текущий объект с подсветкой
        render(sel.value);
      }}
    }}

    function resetScenario(){{
      scenarioMode = false;
      scenarioImpacted = new Set();
      render(sel.value);
    }}

    // === INIT ===
    fillSelect();
    sel.value = "{escape(default_focus)}";
    render(sel.value);

    sel.addEventListener("change", () => {{
      render(sel.value);
    }});

    btnPP1.addEventListener("click", () => {{
      enableScenarioPP1();
    }});

    btnReset.addEventListener("click", () => {{
      resetScenario();
    }});
  </script>
</body>
</html>
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath
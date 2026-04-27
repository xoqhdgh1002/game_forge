#!/usr/bin/env python3
"""
CLI 래퍼 — Sound Agent 실행
사용법: python3 run_sound_agent.py <output_dir>
  <output_dir>/gdd.md + design.md 를 읽어
  <output_dir>/sounds.json 생성 후 exit 0
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.sound_agent import create_sounds

out_dir     = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
gdd_path    = out_dir / "gdd.md"
design_path = out_dir / "design.md"
sounds_path = out_dir / "sounds.json"

if not gdd_path.exists():
    print(f"ERROR: {gdd_path} 없음", file=sys.stderr)
    sys.exit(1)

gdd        = gdd_path.read_text(encoding="utf-8")
# design.md는 없어도 gdd.md만으로 동작 (병렬 실행 시 아직 생성 전일 수 있음)
design_doc = design_path.read_text(encoding="utf-8") if design_path.exists() else ""

result = create_sounds(gdd, design_doc)
if not result:
    # 사운드 생성 실패는 치명적이지 않다 — fallback 파일 생성
    import json
    fallback = {
        "summary": "사운드 생성 실패 — Developer가 기본 비프음을 사용한다",
        "init_code": "let audioCtx = null; function initAudio() { try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e) {} }",
        "bgm_code": "function playBGM() {} function stopBGM() {}",
        "sfx_codes": {
            "jump": "function sfxJump() { try { if(!audioCtx) return; const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.connect(g); g.connect(audioCtx.destination); o.frequency.setValueAtTime(400,audioCtx.currentTime); o.frequency.exponentialRampToValueAtTime(800,audioCtx.currentTime+0.1); g.gain.setValueAtTime(0.3,audioCtx.currentTime); g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+0.15); o.start(); o.stop(audioCtx.currentTime+0.15); } catch(e) {} }",
            "hit": "function sfxHit() { try { if(!audioCtx) return; const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.type='sawtooth'; o.connect(g); g.connect(audioCtx.destination); o.frequency.setValueAtTime(200,audioCtx.currentTime); o.frequency.exponentialRampToValueAtTime(50,audioCtx.currentTime+0.2); g.gain.setValueAtTime(0.4,audioCtx.currentTime); g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+0.2); o.start(); o.stop(audioCtx.currentTime+0.2); } catch(e) {} }",
            "game_over": "function sfxGameOver() { try { if(!audioCtx) return; const notes=[400,300,200,100]; notes.forEach((f,i)=>{ const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.connect(g); g.connect(audioCtx.destination); o.frequency.value=f; g.gain.setValueAtTime(0.3,audioCtx.currentTime+i*0.15); g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+i*0.15+0.14); o.start(audioCtx.currentTime+i*0.15); o.stop(audioCtx.currentTime+i*0.15+0.15); }); } catch(e) {} }",
            "collect": "function sfxCollect() { try { if(!audioCtx) return; const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.connect(g); g.connect(audioCtx.destination); o.frequency.setValueAtTime(600,audioCtx.currentTime); o.frequency.exponentialRampToValueAtTime(1200,audioCtx.currentTime+0.08); g.gain.setValueAtTime(0.2,audioCtx.currentTime); g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+0.1); o.start(); o.stop(audioCtx.currentTime+0.1); } catch(e) {} }",
            "shoot": None,
            "level_up": "function sfxLevelUp() { try { if(!audioCtx) return; const notes=[500,600,700,900]; notes.forEach((f,i)=>{ const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.connect(g); g.connect(audioCtx.destination); o.frequency.value=f; g.gain.setValueAtTime(0.25,audioCtx.currentTime+i*0.1); g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+i*0.1+0.09); o.start(audioCtx.currentTime+i*0.1); o.stop(audioCtx.currentTime+i*0.1+0.1); }); } catch(e) {} }"
        }
    }
    sounds_path.write_text(__import__('json').dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"FALLBACK: sounds.json — 기본 비프음 사용 ({sounds_path})")
    sys.exit(0)

import json
sounds_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK: {sounds_path} — {result.get('summary', '')}")

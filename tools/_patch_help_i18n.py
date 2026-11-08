"""给帮助/反馈对话框接多语言文案。"""

from pathlib import Path

P = Path("src/dota2coach/ui/panel.py")
s = P.read_text(encoding="utf-8")

if "from ..coach.texts_help import htext" not in s:
    s = s.replace(
        "from ..coach.texts import phase_name",
        "from ..coach.texts import language as ui_language, phase_name\nfrom ..coach.texts_help import htext",
        1,
    )

old = '''        text.setText(
            f"""
            <h2>DOTA2 入门教练 v{__version__}</h2>'''
new = '''        if ui_language() == "zh-CN":
            body = f"""
            <p><b>红线</b>：不读内存、不注入、不模拟按键、不改包、不代打。
            只做两件事：接收官方 GSI 报文、截自己屏幕做图像识别。</p>
            <p><b>快捷键</b>：{config.hotkeys.toggle_card} 显示/隐藏卡片；{config.hotkeys.test_voice} 试听语音。</p>
            <p><b>排错</b>：</p>
            <ul>
              <li>状态灯“GSI 监听”不亮：检查 31982 端口是否被旧实例占用。</li>
              <li>“对局中”不亮：游戏里确认启用了 GSI 配置
                  <code>gamestate_integration_coach.cfg</code>。</li>
              <li>“识别 n/10”偏低：确认游戏是窗口/无边框模式，且卡片没挡住顶部英雄栏。</li>
              <li>没有声音：先在设置里把后端改成“在线 edge-tts”，或检查系统音量。</li>
            </ul>
            """
        else:
            body = (
                f"<p>{htext('redline')}</p>"
                f"<p>{htext('hot', toggle=config.hotkeys.toggle_card, voice=config.hotkeys.test_voice)}</p>"
                f"<p>{htext('logs')}</p>"
            )
        text.setText(
            f"""
            <h2>DOTA2 入门教练 v{__version__}</h2>'''
if old not in s:
    raise SystemExit("help anchor 1 missing")
s = s.replace(old, new, 1)

old2 = '''            <p style="color:#6b7280;margin-top:-6px">DOTA2 GETTING STARTED Coach</p>
            <p><b>红线</b>：不读内存、不注入、不模拟按键、不改包、不代打。
            只做两件事：接收官方 GSI 报文、截自己屏幕做图像识别。</p>
            <p><b>快捷键</b>：{config.hotkeys.toggle_card} 显示/隐藏卡片；{config.hotkeys.test_voice} 试听语音。</p>
            <p><b>排错</b>：</p>
            <ul>
              <li>状态灯“GSI 监听”不亮：检查 31982 端口是否被旧实例占用。</li>
              <li>“对局中”不亮：游戏里确认启用了 GSI 配置
                  <code>gamestate_integration_coach.cfg</code>。</li>
              <li>“识别 n/10”偏低：确认游戏是窗口/无边框模式，且卡片没挡住顶部英雄栏。</li>
              <li>没有声音：先在设置里把后端改成“在线 edge-tts”，或检查系统音量。</li>
            </ul>
            <p><b>配置与日志</b>：<br>{config.config_path}<br>{config.log_dir}</p>
            """
        )'''
new2 = '''            <p style="color:#6b7280;margin-top:-6px">DOTA2 GETTING STARTED Coach</p>
            {body}
            <p><b>Config / logs</b>：<br>{config.config_path}<br>{config.log_dir}</p>
            """
        )'''
if old2 not in s:
    raise SystemExit("help anchor 2 missing")
s = s.replace(old2, new2, 1)

s = s.replace('self.setWindowTitle("帮助")', 'self.setWindowTitle(config_title("help"))', 1)

P.write_text(s, encoding="utf-8")
print("help patched")

"""补充“没有具体建议时”的鼓励语（9 语言）。"""

from pathlib import Path

p = Path("src/dota2coach/coach/texts.py")
s = p.read_text(encoding="utf-8")

PAIRS = [
    (
        "输一局没关系，把上面的点做到，下一把就能赢回来！",
        ("赢就是赢，保持这个手感就行。", "输一局没关系，下一把把节奏稳住。"),
    ),
    (
        "輸一局沒關係，把上面的點做到，下一把就能贏回來！",
        ("贏了就好，保持這個手感。", "輸一局沒關係，下一把把節奏穩住。"),
    ),
    (
        "One loss is fine — fix the points above and win the next one!",
        ("A win is a win — keep this feel.", "Losses happen — steady the next one."),
    ),
    (
        "Une défaite n'est rien — corrigez les points ci-dessus et gagnez la suivante !",
        (
            "Une victoire reste une victoire — gardez ce feeling.",
            "Une défaite arrive — gardez le rythme la prochaine fois.",
        ),
    ),
    (
        "Одно поражение не страшно — исправьте пункты выше и выиграйте следующий!",
        (
            "Победа есть победа — сохрани это чувство.",
            "Бывает — в следующей игре держи ритм.",
        ),
    ),
    (
        "Eine Niederlage ist okay — setze die Punkte um und gewinne das nächste!",
        (
            "Sieg ist Sieg — behalte dieses Gefühl.",
            "Niederlagen passieren — bleib im nächsten Spiel ruhig.",
        ),
    ),
    (
        "Uma derrota não é nada — corrija os pontos e ganhe a próxima!",
        (
            "Vitória é vitória — mantenha essa sensação.",
            "Derrotas acontecem — mantenha o ritmo na próxima.",
        ),
    ),
    (
        "Una derrota no es nada: corrige lo de arriba y gana la siguiente.",
        (
            "Victoria es victoria: mantén esta sensación.",
            "Las derrotas pasan: mantén el ritmo la próxima.",
        ),
    ),
    (
        "Bir yenilgi sorun değil — yukarıdakileri düzelt ve sonrakini kazan!",
        ("Kazanmak kazanmaktır — bu hissi koru.", "Kaybetmek olur — sonraki maçta ritmini koru."),
    ),
]

for loss, (win_plain, loss_plain) in PAIRS:
    anchor = f'"encourage_loss": "{loss}",'
    if anchor not in s:
        print("missing anchor:", loss[:20])
        continue
    addition = (
        anchor
        + f'\n        "encourage_win_plain": "{win_plain}",'
        + f'\n        "encourage_loss_plain": "{loss_plain}",'
    )
    s = s.replace(anchor, addition, 1)

p.write_text(s, encoding="utf-8")
print("added plain encouragements")

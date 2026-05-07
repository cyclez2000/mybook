"""CLI entry point for MyBook — AI agent novel writing tool (Sisyphus-driven).

Workflow:
    mybook init <dir>        Initialize a new novel project
    mybook task [--phase X]  Generate the current task for Sisyphus
    mybook status            Show project progress
    mybook compile           Compile all scenes into manuscript.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .config import config
from .task_generator import TaskGenerator
from .bible.manager import BibleManager


@click.group()
@click.version_option(version="0.2.0")
def main():
    """MyBook — AI agent novel writing tool.

    Powered by Sisyphus. No API keys needed.
    
    Workflow:
      1. mybook init my_novel       # Create project
      2. mybook task                # Generate task for current phase
      3. [Give task to Sisyphus]    # Sisyphus writes the files
      4. mybook task                # Next task (repeat until done)
      5. mybook compile             # Export manuscript
    """
    pass


@main.command()
@click.argument("project_dir", type=click.Path(), default="./my_novel")
def init(project_dir: str):
    """Initialize a new novel project directory."""
    proj_path = Path(project_dir).resolve()
    bible = BibleManager(root=proj_path / "bible")
    bible.ensure_dirs()

    click.echo(f"Project created: {proj_path}")
    click.echo(f"")
    click.echo(f"  bible/")
    click.echo(f"    world.md              <- world setting + style sample")
    click.echo(f"    characters/           <- character cards (*.json)")
    click.echo(f"    outline.json          <- 3-act outline + scene plans")
    click.echo(f"    scenes/               <- scene texts (*.md)")
    click.echo(f"    scene_summaries.json  <- scene summaries")
    click.echo(f"    foreshadowing.json    <- foreshadowing table")
    click.echo(f"    timeline.json         <- story timeline")
    click.echo(f"    issues.json           <- review issues")
    click.echo(f"")
    click.echo(f"Next: mybook task  ->  give to Sisyphus  ->  mybook task  ->  ...")


@main.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None,
              help="Project directory")
@click.option("--phase", "-p", type=click.Choice([
    "worldbuilding", "outlining", "writing", "summarizing", "reviewing", "revising"
]), default=None, help="Force a specific phase")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Write task to file (default: .mybook/task.md)")
def task(project_dir: str | None, phase: str | None, output: str | None):
    """Generate the current task for Sisyphus.

    Detects the current phase from bible state and outputs a
    structured Markdown task. Give this task to Sisyphus to execute.
    """
    proj_path = _resolve_project(project_dir)
    gen = TaskGenerator(project_dir=proj_path)

    detected_phase = gen.detect_phase()
    actual_phase = phase or detected_phase

    if phase and phase != detected_phase:
        click.echo(f"Note: forcing phase '{phase}' (auto-detected: '{detected_phase}')")

    task_content = gen.generate_task(phase=actual_phase)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(task_content, encoding="utf-8")
        click.echo(f"Task written to: {out_path}")
    else:
        task_file = gen.write_task_file(phase=actual_phase)
        click.echo(f"Task written to: {task_file}")

    click.echo(f"Phase: {actual_phase}")
    _print_task_summary(task_content)


@main.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None,
              help="Project directory")
def status(project_dir: str | None):
    """Show project progress and bible state."""
    proj_path = _resolve_project(project_dir)
    gen = TaskGenerator(project_dir=proj_path)
    bible = gen.bible

    click.echo(f"Project: {proj_path}")
    click.echo(f"Current phase: {gen.detect_phase()}")
    click.echo(f"")

    if bible.has_world():
        world = bible.read_world()
        click.echo(f"[x] World   ({len(world)} chars)")
    else:
        click.echo(f"[ ] World   (not created)")

    chars = bible.list_characters()
    click.echo(f"[{'x' if chars else ' '}] Characters ({len(chars)})")
    for c in chars:
        char_data = bible.read_character(c)
        role = char_data.get("role", "") if char_data else ""
        click.echo(f"      - {c} ({role})")

    if bible.has_outline():
        outline = bible._load_outline()
        total = outline.total_scenes()
        done = sum(1 for s in outline.iter_scenes() if s.status.value == "done")
        revised = sum(1 for s in outline.iter_scenes() if s.status.value == "revised")
        pending = sum(1 for s in outline.iter_scenes() if s.status.value == "pending")
        click.echo(f"[x] Outline  ({total} scenes: {done} done, {revised} revised, {pending} pending)")
        click.echo(f"      Premise: {outline.premise[:80]}")
    else:
        click.echo(f"[ ] Outline  (not created)")

    fs_table = bible._load_foreshadowing()
    unpaid = fs_table.unpaid()
    click.echo(f"[x] Foreshadowing ({len(fs_table.entries)} total, {len(unpaid)} unpaid)")

    issues = bible._load_issues()
    unresolved = issues.unresolved()
    click.echo(f"[{'!' if unresolved else 'x'}] Issues ({len(unresolved)} unresolved)")
    for i in unresolved:
        click.echo(f"      - [{i.scene_id}] {i.issue_type.value}: {i.description[:60]}")

    click.echo(f"")
    click.echo(f"Next: mybook task")


@main.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None,
              help="Project directory")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output file path (default: manuscript.md)")
def compile(project_dir: str | None, output: str | None):
    """Compile all scenes into a single manuscript file."""
    proj_path = _resolve_project(project_dir)
    bible = BibleManager(root=proj_path / "bible")

    if not bible.has_outline():
        click.echo("No outline found. Cannot compile.", err=True)
        sys.exit(1)

    outline = bible._load_outline()
    out_path = Path(output) if output else proj_path / "manuscript.md"
    lines = []
    scene_num = 0
    total_words = 0

    for act in outline.acts:
        lines.append(f"# Act {act.act}")
        lines.append(f"")
        for chapter in act.chapters:
            chapter_title = chapter.title or f"Chapter {chapter.id}"
            lines.append(f"## {chapter_title}")
            lines.append(f"")
            for scene in chapter.scenes:
                scene_num += 1
                text = bible.read_scene(scene.id)
                if text:
                    lines.append(f"### {scene.id}: {scene.purpose}")
                    lines.append(f"")
                    lines.append(text)
                    lines.append(f"")
                    lines.append(f"---")
                    lines.append(f"")
                    total_words += len(text)

    out_path.write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"Manuscript: {out_path}")
    click.echo(f"  {scene_num} scenes, ~{total_words} chars")


# ═══════════════════════════════════════════════
# Card pool commands (infinite flow extension)
# ═══════════════════════════════════════════════

@main.group()
def card():
    """Manage the instance/skill/item card pool for infinite flow novels."""
    pass


@card.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None)
def pool_init(project_dir: str | None):
    """Initialize the card pool directory with sample cards."""
    proj_path = _resolve_project(project_dir)
    pool_dir = proj_path / "bible" / "instances"
    pool_dir.mkdir(parents=True, exist_ok=True)

    cards_file = pool_dir / "cards.json"
    if cards_file.exists():
        click.echo("Card pool already exists.")
        return

    sample_cards = [
        {
            "id": "inst_001", "name": "恐怖病院", "type": "horror",
            "difficulty": 3, "used": False,
            "premise": "一所废弃的精神病院，每夜12点走廊响起脚步声。墙上用血写着：'别回头'。",
            "rules": ["不能回头看脚步声的来源", "找到六份病历本拼出真相", "天亮前离开"],
            "reward_skills": ["灵视（初级）"],
            "reward_items": ["破损的手术刀"],
            "boss": "第7号病人——一个不存在于病历上的'人'"
        },
        {
            "id": "inst_002", "name": "赛博废墟", "type": "scifi",
            "difficulty": 4, "used": False,
            "premise": "2077年，AI叛乱后的钢铁城市。所有数据流中都夹着一个文明的求救信号。",
            "rules": ["不能接入公共网络", "找到AI核心并注入病毒", "72小时内离开"],
            "reward_skills": ["数据感知"],
            "reward_items": ["神经元接口"],
            "boss": "'母亲'——控制全城网络的超级AI，但它似乎在哭"
        },
        {
            "id": "inst_003", "name": "镜中公寓", "type": "mystery",
            "difficulty": 2, "used": False,
            "premise": "一栋永远只有13户的公寓楼。每面镜子里，你都不是在照自己——是在看某个房客的最后一天。",
            "rules": ["不能在镜子里看自己超过3秒", "找到第14户的钥匙", "午夜前离开"],
            "reward_skills": ["镜面穿行"],
            "reward_items": ["半面镜子"],
            "boss": "不存在于任何镜中的'房东'"
        },
        {
            "id": "inst_004", "name": "明朝诏狱", "type": "historical",
            "difficulty": 5, "used": False,
            "premise": "万历年间诏狱。每一个囚犯都声称自己是被冤枉的——但诏狱里没有无辜之人。",
            "rules": ["不能暴露穿越者身份", "找出真正的诏狱典狱长", "活着走出诏狱大门"],
            "reward_skills": ["历史直觉"],
            "reward_items": ["锦衣卫腰牌"],
            "boss": "典狱长——他的脸和你一样"
        },
        {
            "id": "inst_005", "name": "深海钻井平台", "type": "survival",
            "difficulty": 4, "used": False,
            "premise": "暴风雨中与外界失联的钻井平台。水下有什么东西在敲击支柱——敲了三百年了。",
            "rules": ["不能单独行动", "每次下水不超过20分钟", "找到'源头'"],
            "reward_skills": ["水下呼吸"],
            "reward_items": ["深海结晶"],
            "boss": "平台最深处关着的'东西'——它不是被关进去的，是它自己在等"
        },
    ]

    import json
    cards_file.write_text(json.dumps(sample_cards, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"Card pool initialized: {len(sample_cards)} instance cards")
    click.echo(f"  {cards_file}")


@card.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None)
@click.option("--count", "-n", type=int, default=1, help="Number of cards to draw")
def draw(project_dir: str | None, count: int):
    """Randomly draw unused instance cards from the pool."""
    proj_path = _resolve_project(project_dir)
    cards_file = proj_path / "bible" / "instances" / "cards.json"

    if not cards_file.exists():
        click.echo("No card pool found. Run 'mybook card pool-init' first.")
        return

    import json, random
    cards = json.loads(cards_file.read_text(encoding="utf-8"))
    unused = [c for c in cards if not c.get("used", False)]

    if not unused:
        click.echo("All cards have been used!")
        return

    if count > len(unused):
        count = len(unused)

    drawn = random.sample(unused, count)
    for c in drawn:
        c["used"] = True

    cards_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    click.echo(f"Drew {count} card(s):")
    for c in drawn:
        click.echo(f"  [{c['id']}] {c['name']} (difficulty: {c['difficulty']})")
        click.echo(f"    {c['premise'][:80]}")


@card.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None)
def list(project_dir: str | None):
    """List all cards and their used/unused status."""
    proj_path = _resolve_project(project_dir)
    cards_file = proj_path / "bible" / "instances" / "cards.json"

    if not cards_file.exists():
        click.echo("No card pool found. Run 'mybook card pool-init' first.")
        return

    import json
    cards = json.loads(cards_file.read_text(encoding="utf-8"))
    used = sum(1 for c in cards if c.get("used", False))
    unused = sum(1 for c in cards if not c.get("used", False))

    click.echo(f"Card pool: {len(cards)} total ({unused} unused, {used} used)")
    click.echo("")
    for c in cards:
        status = "[USED]" if c.get("used") else "[AVAIL]"
        click.echo(f"  {status} {c['id']}: {c['name']} (diff: {c['difficulty']})")


@card.command()
@click.option("--project-dir", "-d", type=click.Path(exists=True), default=None)
@click.option("--name", "-n", required=True, help="Card name")
@click.option("--type", "-t", required=True, help="horror/scifi/mystery/historical/survival/other")
@click.option("--difficulty", "-l", type=int, required=True, help="Difficulty 1-10")
@click.option("--premise", "-p", required=True, help="One-line premise")
def add_instance(project_dir, name, type, difficulty, premise):
    """Add a new instance card to the pool."""
    proj_path = _resolve_project(project_dir)
    cards_file = proj_path / "bible" / "instances" / "cards.json"

    import json
    cards = json.loads(cards_file.read_text(encoding="utf-8")) if cards_file.exists() else []
    new_id = f"inst_{len(cards) + 1:03d}"

    cards.append({
        "id": new_id, "name": name, "type": type,
        "difficulty": difficulty, "used": False,
        "premise": premise,
        "rules": [], "reward_skills": [], "reward_items": [], "boss": ""
    })
    cards_file.parent.mkdir(parents=True, exist_ok=True)
    cards_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"Added: [{new_id}] {name}")


def _resolve_project(project_dir: str | None) -> Path:
    if project_dir:
        return Path(project_dir).resolve()
    if config.project_dir:
        return Path(config.project_dir).resolve()
    return Path("./my_novel").resolve()


def _print_task_summary(content: str) -> None:
    lines = content.split("\n")
    in_instructions = False
    for line in lines:
        if line.startswith("## 任务指令"):
            in_instructions = True
            continue
        if in_instructions and line.startswith("## "):
            break
        if in_instructions and line.strip() and line.strip()[0].isdigit():
            click.echo(f"  {line.strip()}")


if __name__ == "__main__":
    main()

import logging
import os
from typing import Tuple


logger = logging.getLogger(__name__)


def to_ascii(tree) -> str:
    """Return a human-readable ASCII representation of the tree.

    Relies on nutree.Tree.format() and each node's __str__ implementation.
    """
    return tree.format()


def _wrap(text: str, width: int) -> str:
    if not text:
        return ""
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + (1 if cur else 0) + len(w) > width:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += (1 if cur_len else 0) + len(w)
    if cur:
        lines.append(" ".join(cur))
    return "\n".join(lines)


def _node_label(issue) -> Tuple[str, dict]:
    """Build a readable multi-line label and style for a Graphviz node.

    Label includes: key, status, and wrapped title for readability.
    Returns (label, attrs) where attrs can contain color/style tuning.
    """
    key = getattr(issue, 'key', '')
    status = getattr(issue, 'status', '')
    title = getattr(issue, 'title', '')
    title_wrapped = _wrap(title, width=28)
    label = f"{key}\n{status}\n{title_wrapped}"

    # Default styling
    attrs = {
        'shape': 'box',
        'style': 'rounded,filled',
        'fontsize': '10',
        'fontname': 'Arial',
        'fillcolor': 'white',
        'color': 'gray40',
    }

    # Color-coding by type for scanability (soft colors for legibility)
    issue_type = getattr(issue, 'type', '')
    project = getattr(issue, 'project', '')
    if project == 'LVL2' and issue_type == 'Epic LPM':
        attrs['fillcolor'] = '#E7F7E7'  # light green
    elif project == 'LVL2' and issue_type == 'New Feature':
        attrs['fillcolor'] = '#FFF7CC'  # light yellow
    elif project == 'PCI' and issue_type == 'Epic':
        attrs['fillcolor'] = '#E6F0FF'  # light blue
    elif project == 'PCI' and issue_type in ('Story', 'Task'):
        attrs['fillcolor'] = '#F5F5F5'  # light gray

    return label, attrs


def render_graph(tree, *, out_dir: str = './out', filename: str = 'lsd-tree', fmt: str = 'png', open_view: bool = True) -> str:
    """Render the tree to a Graphviz graph, save to disk, and optionally open it.

    - Node labels: key + status + wrapped title (readable in boxes).
    - Layout: top-to-bottom tree.
    - Returns the path (without extension) to the generated file from graphviz.
    """
    # Lazy import so graphviz is optional unless rendering
    try:
        from graphviz import Digraph  # type: ignore
    except Exception as e:
        logger.error('Graphviz package is required for render_graph: %s', e)
        raise

    os.makedirs(out_dir, exist_ok=True)

    dot = Digraph('LSD', format=fmt)
    dot.attr(rankdir='TB', fontsize='12', fontname='Arial')

    # We need stable ids for nodes; use incremental indices during traversal
    id_map = {}
    counter = 0

    # First pass: create all nodes
    for node in tree:
        nid = id_map.setdefault(id(node), f'n{counter}')
        if nid == f'n{counter}':
            counter += 1
        label, attrs = _node_label(node.data)
        dot.node(nid, label=label, **attrs)

    # Second pass: create edges (parent -> children)
    def walk(n):
        pid = id_map[id(n)]
        for child in n:
            cid = id_map[id(child)]
            dot.edge(pid, cid, color='gray60')
            walk(child)

    # root(s) are children of the Tree object; detect by nodes without parents
    # nutree.Tree is iterable depth-first; we can start from the real root (tree.root)
    try:
        root = tree.root
    except Exception:
        root = None
    if root is not None:
        walk(root)
    else:
        # Fallback: no explicit root attribute; best-effort pass over first-level nodes
        for node in tree:
            for child in node:
                dot.edge(id_map[id(node)], id_map[id(child)], color='gray60')

    out_path = os.path.join(out_dir, filename)
    logger.info('Rendering graph to %s.%s', out_path, fmt)
    saved = dot.render(out_path, cleanup=True)

    if open_view:
        try:
            dot.view(out_path, cleanup=False)
        except Exception as e:
            logger.warning('Failed to open viewer: %s', e)

    return saved

importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/wheels/bokeh-3.6.1-py3-none-any.whl', 'https://cdn.holoviz.org/panel/1.5.4/dist/wheels/panel-1.5.4-py3-none-any.whl', 'pyodide-http==0.2.1', 'numpy', 'pandas']
  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  \nimport asyncio\n\nfrom panel.io.pyodide import init_doc, write_doc\n\ninit_doc()\n\nfrom panel import state as _pn__state\nfrom panel.io.handlers import CELL_DISPLAY as _CELL__DISPLAY, display, get_figure as _get__figure\n\nimport json\nimport numpy as np\nimport pandas as pd\nimport panel as pn\n\npn.extension('deckgl', template='fast', sizing_mode="stretch_width")\n\n_pn__state._cell_outputs['8e42671c'].append((pn.state.template.param.update(\n    title="Deck.gl - Game of Life",\n    main_max_width="768px"\n)))\nfor _cell__out in _CELL__DISPLAY:\n    _pn__state._cell_outputs['8e42671c'].append(_cell__out)\n_CELL__DISPLAY.clear()\n_fig__out = _get__figure()\nif _fig__out:\n    _pn__state._cell_outputs['8e42671c'].append(_fig__out)\n\n_pn__state._cell_outputs['29e2c280'].append("""This demo was adapted from [PyDeck's Conway Game of Life example](https://github.com/uber/deck.gl/blob/66c75051d5b385db31f0a4322dff054779824783/bindings/pydeck/examples/06%20-%20Conway's%20Game%20of%20Life.ipynb), full copyright lies with the original authors.\n\nThis modified example demonstrates how to display and update a \`DeckGL\` pane with a periodic callback by modifying the JSON representation and triggering an update.""")\n_pn__state._cell_outputs['f83267eb'].append("""## Declare Game of Life logic""")\nimport random\n\ndef new_board(x, y, num_live_cells=2, num_dead_cells=3):\n    """Initializes a board for Conway's Game of Life"""\n    board = []\n    for i in range(0, y):\n        # Defaults to a 3:2 dead cell:live cell ratio\n        board.append([random.choice([0] * num_dead_cells + [1] * num_live_cells) for _ in range(0, x)])\n    return board\n\n        \ndef get(board, x, y):\n    """Return the value at location (x, y) on a board, wrapping around if out-of-bounds"""\n    return board[y % len(board)][x % len(board[0])]\n\n\ndef assign(board, x, y, value):\n    """Assigns a value at location (x, y) on a board, wrapping around if out-of-bounds"""\n    board[y % len(board)][x % len(board[0])] = value\n\n\ndef count_neighbors(board, x, y):\n    """Counts the number of living neighbors a cell at (x, y) on a board has"""\n    return sum([\n        get(board, x - 1, y),\n        get(board, x + 1, y),\n        get(board, x, y - 1),\n        get(board, x, y + 1),\n        get(board, x + 1, y + 1),\n        get(board, x + 1, y - 1),\n        get(board, x - 1, y + 1),\n        get(board, x - 1, y - 1)])\n\n\ndef process_life(board):\n    """Creates the next iteration from a passed state of Conway's Game of Life"""\n    next_board = new_board(len(board[0]), len(board))\n    for y in range(0, len(board)):\n        for x in range(0, len(board[y])):\n            num_neighbors = count_neighbors(board, x, y)\n            is_alive = get(board, x, y) == 1\n            if num_neighbors < 2 and is_alive:\n                assign(next_board, x, y, 0)\n            elif 2 <= num_neighbors <= 3 and is_alive:\n                assign(next_board, x, y, 1)\n            elif num_neighbors > 3 and is_alive:\n                assign(next_board, x, y, 0)\n            elif num_neighbors == 3 and not is_alive:\n                assign(next_board, x, y, 1)\n            else:\n                assign(next_board, x, y, 0)\n    return next_board\n_pn__state._cell_outputs['8b58ac30'].append("""## Set up DeckGL JSON""")\npoints = {\n    '@@type': 'PointCloudLayer',\n    'data': [],\n    'getColor': '@@=color',\n    'getPosition': '@@=position',\n    'getRadius': 40,\n    'id': '0558257e-1a5c-43d7-bd98-1fba69981c6c'\n}\n\nboard_json = {\n    "initialViewState": {\n        "bearing": 44,\n        "latitude": 0.01,\n        "longitude": 0.01,\n        "pitch": 45,\n        "zoom": 13\n    },\n    "layers": [points],\n    "mapStyle": None,\n    "views": [\n        {\n            "@@type": "MapView",\n            "controller": True\n        }\n    ]\n}\n_pn__state._cell_outputs['e67ca14f'].append("""## Declare callbacks to periodically update the board""")\nPINK = [155, 155, 255, 245]\nPURPLE = [255, 155, 255, 245]\n\nSCALING_FACTOR = 1000.0\n\ndef convert_board_to_df(board):\n    """Makes the board matrix into a list for easier processing"""\n    rows = []\n    for x in range(0, len(board[0])):\n        for y in range(0, len(board)):\n            rows.append([[x / SCALING_FACTOR, y / SCALING_FACTOR], PURPLE if board[y][x] else PINK])\n    return pd.DataFrame(rows, columns=['position', 'color'])\n\ndef run_gol(event=None):\n    global board\n    board = process_life(board)\n    records = convert_board_to_df(board)\n    points['data'] = records\n    gol.param.trigger('object')\n    \ndef reset_board(event):\n    global board\n    board = new_board(30, 30)\n    run_gol()\n\ndef toggle_periodic_callback(event):\n    if event.new:\n        periodic_toggle.name = 'Stop'\n        periodic_toggle.button_type = 'warning'\n        periodic_cb.start()\n    else:\n        periodic_toggle.name = 'Run'\n        periodic_toggle.button_type = 'primary'\n        periodic_cb.stop()\n        \ndef update_period(event):\n    periodic_cb.period = event.new\n_pn__state._cell_outputs['2d427e6b'].append("""## Set up Panel and callbacks""")\nboard = new_board(30, 30)\n\ngol = pn.pane.DeckGL(board_json, height=400)\n\nrun_gol()\n\nperiodic_toggle = pn.widgets.Toggle(\n    name='Run', value=False, button_type='primary', align='end', width=50\n)\nperiodic_toggle.param.watch(toggle_periodic_callback, 'value')\n\nperiod = pn.widgets.Spinner(name="Period (ms)", value=500, step=50, start=50,\n                            align='end', width=100)\nperiod.param.watch(update_period, 'value')\n\nreset = pn.widgets.Button(name='Reset', button_type='warning', width=60, align='end')\nreset.on_click(reset_board)\n\nperiodic_cb = pn.state.add_periodic_callback(run_gol, start=False, period=period.value)\n\nsettings = pn.Row(period, periodic_toggle, reset, width=400, sizing_mode="fixed")\n\ndescription = """\n**Conway's Game of Life** is a classic demonstration of *emergence*, where higher level patterns form from a few simple rules. Fantastic patterns emerge when the game is let to run long enough.\n\nThe **rules** here, to borrow from [Wikipedia](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life), are as follows:\n\n- Any live cell with fewer than two live neighbours dies, as if by underpopulation.\n- Any live cell with two or three live neighbours lives on to the next generation.\n- Any live cell with more than three live neighbours dies, as if by overpopulation.\n- Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.\n\nThis demo was **adapted from [PyDeck's Conway Game of Life example](https://github.com/uber/deck.gl/blob/66c75051d5b385db31f0a4322dff054779824783/bindings/pydeck/examples/06%20-%20Conway's%20Game%20of%20Life.ipynb)**, full copyright lies with the original authors.\n\nThis modified example demonstrates **how to display and update a \`DeckGL\` pane with a periodic callback** by modifying the JSON representation and triggering an update."""\n\n_pn__state._cell_outputs['ebec04b6'].append((pn.Column(\n    '## Game of Life (using Deck.GL)',\n    pn.Column(\n        description,\n        gol,\n        settings\n    ).servable()\n)))\nfor _cell__out in _CELL__DISPLAY:\n    _pn__state._cell_outputs['ebec04b6'].append(_cell__out)\n_CELL__DISPLAY.clear()\n_fig__out = _get__figure()\nif _fig__out:\n    _pn__state._cell_outputs['ebec04b6'].append(_fig__out)\n\n\nawait write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.globals.set('patch', msg.patch)
    self.pyodide.runPythonAsync(`
    from panel.io.pyodide import _convert_json_patch
    state.curdoc.apply_json_patch(_convert_json_patch(patch), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.globals.set('location', msg.location)
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads(location)
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()
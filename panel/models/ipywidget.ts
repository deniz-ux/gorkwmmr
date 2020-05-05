import * as p from "@bokehjs/core/properties"
import {HTMLBox} from "@bokehjs/models/layouts/html_box"

import {PanelHTMLBoxView} from "./layout"

const Jupyter = (window as any).Jupyter

export class IPyWidgetView extends PanelHTMLBoxView {
  model: IPyWidget
  private rendered: boolean = false

  render(): void {
    super.render()
    if (!this.rendered) {
      this._render().then(() => {
        this.rendered = true
        this.invalidate_layout()
        this.notify_finished()
      })
    }
  }

  has_finished(): boolean {
    return this.rendered && super.has_finished()
  }

  async _render(): Promise<void> {
    const {spec, state} = this.model.bundle
    let manager: any
	let model: any
    if ((Jupyter != null) && (Jupyter.notebook != null))
      manager = Jupyter.notebook.kernel.widget_manager
    else if ((window as any).PyViz.widget_manager != null)
      manager = (window as any).PyViz.widget_manager
    if (!manager) {
      console.log("Panel IPyWidget model could not find a WidgetManager")
      return
    }
	const models = await manager.set_state(state)
      model = models.find((item: any) => item.model_id == spec.model_id)
    if (model != null) {
	  const view = await manager.create_view(model);
	  this.el.appendChild(view.el)
    }
  }
}

export namespace IPyWidget {
  export type Attrs = p.AttrsOf<Props>
  export type Props = HTMLBox.Props & {
    bundle: p.Property<any>
  }
}

export interface IPyWidget extends IPyWidget.Attrs {}

export class IPyWidget extends HTMLBox {
  properties: IPyWidget.Props

  constructor(attrs?: Partial<IPyWidget.Attrs>) {
    super(attrs)
  }

  static __module__ = "panel.models.ipywidget"

  static init_IPyWidget(): void {
    this.prototype.default_view = IPyWidgetView

    this.define<IPyWidget.Props>({
      bundle: [ p.Any, {} ],
    })
  }
}

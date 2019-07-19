import * as p from "core/properties"
import {clone} from "core/util/object"
import {HTMLBox, HTMLBoxView} from "models/layouts/html_box"


function isPlainObject (obj: any) {
	return Object.prototype.toString.call(obj) === '[object Object]';
}

interface PlotlyHTMLElement extends HTMLElement {
    on(event: 'plotly_relayout', callback: (eventData: any) => void): void;
    on(event: 'plotly_restyle', callback: (eventData: any) => void): void;
    on(event: 'plotly_click', callback: (eventData: any) => void): void;
    on(event: 'plotly_hover', callback: (eventData: any) => void): void;
    on(event: 'plotly_clickannotation', callback: (eventData: any) => void): void;
    on(event: 'plotly_selected', callback: (eventData: any) => void): void;
    on(event: 'plotly_deselect', callback: () => void): void;
    on(event: 'plotly_unhover', callback: () => void): void;
}

const filterEventData = (gd: any, eventData: any, event: string) => {
    // Ported from dash-core-components/src/components/Graph.react.js
    let filteredEventData: {[k: string]: any} = Array.isArray(eventData)? []: {};

    if (event === "click" || event === "hover" || event === "selected") {
        const points = [];

        if (eventData === undefined || eventData === null) {
            return null;
        }

        /*
         * remove `data`, `layout`, `xaxis`, etc
         * objects from the event data since they're so big
         * and cause JSON stringify ciricular structure errors.
         *
         * also, pull down the `customdata` point from the data array
         * into the event object
         */
        const data = gd.data;

        for (let i = 0; i < eventData.points.length; i++) {
            const fullPoint = eventData.points[i];

            let pointData: {[k: string]: any} = {};
            for (let property in fullPoint) {
              const val = fullPoint[property];
              if (fullPoint.hasOwnProperty(property) &&
                  !Array.isArray(val) && !isPlainObject(val))  {

                pointData[property] = val;
              }
            }

            if (fullPoint !== undefined && fullPoint !== null) {
              if(fullPoint.hasOwnProperty("curveNumber") &&
                  fullPoint.hasOwnProperty("pointNumber") &&
                  data[fullPoint["curveNumber"]].hasOwnProperty("customdata")) {

                pointData["customdata"] =
                    data[fullPoint["curveNumber"]].customdata[
                        fullPoint["pointNumber"]
                    ]
              }

              // specific to histogram. see https://github.com/plotly/plotly.js/pull/2113/
              if (fullPoint.hasOwnProperty('pointNumbers')) {
                  pointData["pointNumbers"] = fullPoint.pointNumbers;
              }
            }

            points[i] = pointData;
        }
        filteredEventData["points"] = points;
    } else if (event === 'relayout' || event === 'restyle') {
        /*
         * relayout shouldn't include any big objects
         * it will usually just contain the ranges of the axes like
         * "xaxis.range[0]": 0.7715822247381828,
         * "xaxis.range[1]": 3.0095292008680063`
         */
        for (let property in eventData) {
              if (eventData.hasOwnProperty(property))  {
                filteredEventData[property] = eventData[property];
              }
        }
    }
    if (eventData.hasOwnProperty('range')) {
        filteredEventData["range"] = eventData["range"];
    }
    if (eventData.hasOwnProperty('lassoPoints')) {
        filteredEventData["lassoPoints"] = eventData["lassoPoints"];
    }
    return filteredEventData;
};

export class PlotlyPlotView extends HTMLBoxView {
  model: PlotlyPlot
  _connected: string[]

  connect_signals(): void {
    super.connect_signals();
    this.connect(this.model.properties.data.change, this.render);
    this.connect(this.model.properties.layout.change, this._relayout);
    this.connect(this.model.properties.config.change, this.render);
    this.connect(this.model.properties.data_sources.change, () => this._connect_sources());

    this._connected = [];
    this._connect_sources();
  }

  _connect_sources(): void {
    for (let i = 0; i < this.model.data.length; i++) {
      const cds = this.model.data_sources[i]
      if (this._connected.indexOf(cds.id) < 0) {
        this.connect(cds.properties.data.change, () => this._restyle(i))
        this._connected.push(cds.id)
      }
    }
  }

  render(): void {
    super.render()
    if (!(window as any).Plotly) { return }
    if (!this.model.data.length && !Object.keys(this.model.layout).length) {
      (window as any).Plotly.purge(this.el);
    }
    const data = [];
    for (let i = 0; i < this.model.data.length; i++) {
      data.push(this._get_trace(i, false));
    }

    (window as any).Plotly.react(this.el, data, this.model.layout, this.model.config);

    // Install callbacks
    //  - plotly_relayout
    (<PlotlyHTMLElement>(this.el)).on('plotly_relayout', (eventData: any) => {
      this.model.relayout_data = filterEventData(
          this.el, eventData, 'relayout');
    });

    //  - plotly_restyle
    (<PlotlyHTMLElement>(this.el)).on('plotly_restyle', (eventData: any) => {
      this.model.restyle_data = filterEventData(
          this.el, eventData, 'restyle');
    });

    //  - plotly_click
    (<PlotlyHTMLElement>(this.el)).on('plotly_click', (eventData: any) => {
      this.model.click_data = filterEventData(
          this.el, eventData, 'click');
    });

    //  - plotly_hover
    (<PlotlyHTMLElement>(this.el)).on('plotly_hover', (eventData: any) => {
      this.model.hover_data = filterEventData(
          this.el, eventData, 'hover');
    });

    //  - plotly_selected
    (<PlotlyHTMLElement>(this.el)).on('plotly_selected', (eventData: any) => {
      this.model.selected_data = filterEventData(
          this.el, eventData, 'selected');
    });

    //  - plotly_clickannotation
    (<PlotlyHTMLElement>(this.el)).on('plotly_clickannotation', (eventData: any) => {
      delete eventData["event"];
      delete eventData["fullAnnotation"];
      this.model.clickannotation_data = eventData
    });

    //  - plotly_deselect
    (<PlotlyHTMLElement>(this.el)).on('plotly_deselect', () => {
      this.model.selected_data = null;
    });

    //  - plotly_unhover
    (<PlotlyHTMLElement>(this.el)).on('plotly_unhover', () => {
      this.model.hover_data = null;
    });
  }

  _get_trace(index: number, update: boolean): any {
    const trace = clone(this.model.data[index]);
    const cds = this.model.data_sources[index];
    for (const column of cds.columns()) {
      const shape: number[] = cds._shapes[column][0];
      let array = cds.get_array(column)[0];
      if (shape.length > 1) {
        const arrays = [];
        for (let s = 0; s < shape[0]; s++) {
          arrays.push(array.slice(s*shape[1], (s+1)*shape[1]));
        }
        array = arrays;
      }
      let prop_path = column.split(".");
      let prop = prop_path[prop_path.length - 1];
      var prop_parent = trace;
      for(let k of prop_path.slice(0, -1)) {
        prop_parent = prop_parent[k]
      }

      if (update) {
        prop_parent[prop] = [array];
      } else {
        prop_parent[prop] = array;
      }
    }
    return trace;
  }

  _restyle(index: number): void {
    if (!(window as any).Plotly) { return }
    const trace = this._get_trace(index, true);

    (window as any).Plotly.restyle(this.el, trace, index)
  }

  _relayout(): void {
    if (!(window as any).Plotly) { return }

    (window as any).Plotly.relayout(this.el, this.model.layout)
  }
}

export namespace PlotlyPlot {
  export type Attrs = p.AttrsOf<Props>
  export type Props = HTMLBox.Props & {
    data: p.Property<any[]>
    layout: p.Property<any>
    config: p.Property<any>
    data_sources: p.Property<any[]>
    relayout_data: p.Property<any>
    restyle_data: p.Property<any>
    click_data: p.Property<any>
    hover_data: p.Property<any>
    clickannotation_data: p.Property<any>
    selected_data: p.Property<any>
  }
}

export interface PlotlyPlot extends PlotlyPlot.Attrs {}

export class PlotlyPlot extends HTMLBox {
  properties: PlotlyPlot.Props

  constructor(attrs?: Partial<PlotlyPlot.Attrs>) {
    super(attrs)
  }

  static initClass(): void {
    this.prototype.type = "PlotlyPlot"
    this.prototype.default_view = PlotlyPlotView

    this.define<PlotlyPlot.Props>({
      data: [ p.Array, [] ],
      layout: [ p.Any, {} ],
      config: [ p.Any, {} ],
      data_sources: [ p.Array, [] ],
      relayout_data: [ p.Any, {} ],
      restyle_data: [ p.Array, [] ],
      click_data: [ p.Any, {} ],
      hover_data: [ p.Any, {} ],
      clickannotation_data: [ p.Any, {} ],
      selected_data: [ p.Any, {} ],
    })
  }
}
PlotlyPlot.initClass()

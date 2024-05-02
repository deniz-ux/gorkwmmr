import {InputWidget, InputWidgetView} from "@bokehjs/models/widgets/input_widget"
import type {StyleSheetLike} from "@bokehjs/core/dom"
import {input} from "@bokehjs/core/dom"
import {isString} from "@bokehjs/core/util/types"
import * as p from "@bokehjs/core/properties"
import * as inputs from "@bokehjs/styles/widgets/inputs.css"
import buttons_css from "@bokehjs/styles/buttons.css"

export class FileInputView extends InputWidgetView {
  declare model: FileInput
  declare input_el: HTMLInputElement

  override stylesheets(): StyleSheetLike[] {
    return [...super.stylesheets(), buttons_css]
  }

  protected _render_input(): HTMLElement {
    const {multiple, disabled, directory} = this.model

    const accept = (() => {
      const {accept} = this.model
      return isString(accept) ? accept : accept.join(",")
    })()

    return this.input_el = input({type: "file", class: inputs.input, multiple, accept, disabled, webkitdirectory: directory})
  }

  override connect_signals(): void {
    super.connect_signals()
    const {_clear_input} = this.model.properties
    this.on_change(_clear_input, this.clear_input)
  }

  override render(): void {
    super.render()

    this.input_el.addEventListener("change", async () => {
      const {files} = this.input_el
      if (files != null) {
        await this.load_files(files)
      }
    })
  }

  async load_files(files: FileList): Promise<void> {
    const values: string[] = []
    const filenames: string[] = []
    const mime_types: string[] = []
    const {directory, multiple} = this.model

    for (const file of files) {
      const data_url = await this._read_file(file)
      const [, mime_type="",, value=""] = data_url.split(/[:;,]/, 4)

      values.push(value)
      mime_types.push(mime_type)
      if (directory) {
        filenames.push(file.webkitRelativePath)
      } else {
        filenames.push(file.name)
      }
    }

    const [value, filename, mime_type] = (() =>{
      if (directory || multiple) {
        return [values, filenames, mime_types]
      } else if (files.length != 0) {
        return [values[0], filenames[0], mime_types[0]]
      } else {
        return ["", "", ""]
      }
    })()

    this.model.setv({value, filename, mime_type})
  }

  protected _read_file(file: File): Promise<string> {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const {result} = reader
        if (result != null) {
          resolve(result as string)
        } else {
          reject(reader.error ?? new Error(`unable to read '${file.name}'`))
        }
      }
      reader.readAsDataURL(file)
    })
  }
  protected clear_input(): void {
    this.input_el.value = ""
    this.model.setv({value: "", filename: "", mime_type: ""})
  }

}

export namespace FileInput {
  export type Attrs = p.AttrsOf<Props>
  export type Props = InputWidget.Props & {
    value: p.Property<string | string[]>
    mime_type: p.Property<string | string[]>
    filename: p.Property<string | string[]>
    accept: p.Property<string | string[]>
    multiple: p.Property<boolean>
    directory: p.Property<boolean>
    _clear_input: p.Property<number>
  }
}

export interface FileInput extends FileInput.Attrs {}

export class FileInput extends InputWidget {
  declare properties: FileInput.Props
  declare __view_type__: FileInputView

  constructor(attrs?: Partial<FileInput.Attrs>) {
    super(attrs)
  }

  static override __module__ = "panel.models.widgets"

  static {
    this.prototype.default_view = FileInputView

    this.define<FileInput.Props>(({Bool, Str, List, Or, Int}) => ({
      value:     [ Or(Str, List(Str)), p.unset, {readonly: true} ],
      mime_type: [ Or(Str, List(Str)), p.unset, {readonly: true} ],
      filename:  [ Or(Str, List(Str)), p.unset, {readonly: true} ],
      accept:    [ Or(Str, List(Str)), "" ],
      multiple:  [ Bool, false ],
      directory: [ Bool, false ],
      _clear_input: [ Int, 0],
    }))
  }
}

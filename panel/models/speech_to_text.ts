import * as p from "@bokehjs/core/properties"
import { HTMLBox, HTMLBoxView } from "@bokehjs/models/layouts/html_box"

const iconStarted = `<svg xmlns="http://www.w3.org/2000/svg" height="22px" style="vertical-align: middle;" fill="currentColor" class="bi bi-mic" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5z"/>
  <path fill-rule="evenodd" d="M10 8V3a2 2 0 1 0-4 0v5a2 2 0 1 0 4 0zM8 0a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V3a3 3 0 0 0-3-3z"/>
</svg>`
const iconNotStarted = `<svg xmlns="http://www.w3.org/2000/svg" height="22px" style="vertical-align: middle;" fill="currentColor" class="bi bi-mic-mute" viewBox="0 0 16 16">
<path fill-rule="evenodd" d="M12.734 9.613A4.995 4.995 0 0 0 13 8V7a.5.5 0 0 0-1 0v1c0 .274-.027.54-.08.799l.814.814zm-2.522 1.72A4 4 0 0 1 4 8V7a.5.5 0 0 0-1 0v1a5 5 0 0 0 4.5 4.975V15h-3a.5.5 0 0 0 0 1h7a.5.5 0 0 0 0-1h-3v-2.025a4.973 4.973 0 0 0 2.43-.923l-.718-.719zM11 7.88V3a3 3 0 0 0-5.842-.963l.845.845A2 2 0 0 1 10 3v3.879l1 1zM8.738 9.86l.748.748A3 3 0 0 1 5 8V6.121l1 1V8a2 2 0 0 0 2.738 1.86zm4.908 3.494l-12-12 .708-.708 12 12-.708.707z"/>
</svg>`

const titleStarted = "Click to STOP the speech recognition.";
const titleNotStarted = "Click to START the speech recognition.";

// Hack inspired by https://stackoverflow.com/questions/38087013/angular2-web-speech-api-voice-recognition
interface IWindow extends Window {
    webkitSpeechRecognition: any;
    webkitSpeechGrammarList: any;
}
const {webkitSpeechRecognition} : IWindow = <IWindow><unknown>window;
const {webkitSpeechGrammarList} : IWindow = <IWindow><unknown>window;

function htmlToElement(html: string) {
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return <HTMLElement>template.content.firstChild;
}

function deserializeGrammars(grammars: any[]){
    if (grammars){
        var speechRecognitionList = new webkitSpeechGrammarList();
        for (let grammar of grammars){
            if (grammar.src){
                speechRecognitionList.addFromString(grammar.src, grammar.weight)
            } else if (grammar.uri) {
                speechRecognitionList.addFromURI(grammar.uri, grammar.weight)
            }
        }
        return speechRecognitionList
    } else {
        return null;
    }
}

function serializeResults(results_: any) {
    const results = [];
    for (let result of results_) {
        let alternatives: { confidence: number; transcript: string; }[] = [];
        let item = { is_final: result.isFinal, alternatives: alternatives };
        for (let i = 0; i < result.length; i++) {
            let alternative = { confidence: result[i].confidence, transcript: result[i].transcript };
            alternatives.push(alternative);
        }
        item.alternatives = alternatives;
        results.push(item);
    }
    return results;
}

export class SpeechToTextView extends HTMLBoxView {
    model: SpeechToText
    recognition: any
    buttonEl: HTMLElement

    initialize(): void {
        super.initialize()

        this.recognition = new webkitSpeechRecognition();
        this.setGrammars()
        const this_ = this;

        this.recognition.onresult = function(event: any) {
            this_.model.results=serializeResults(event.results);
          }
        this.recognition.onerror = function(event: any) {
            console.log("SpeechToText Error")
            console.log(event);
        }
        this.recognition.onnomatch = function(event: any){
            console.log("SpeechToText No Match")
            console.log(event)
        }

        this.recognition.onaudiostart = () => {this_.model.audio_started=true}
        this.recognition.onaudioend = () => {this_.model.audio_started=false}
        this.recognition.onsoundstart = () => {this.model.sound_started=true}
        this.recognition.onsoundend = () => {this_.model.sound_started=false}
        this.recognition.onspeechstart = () => {this_.model.speech_started=true}
        this.recognition.onspeechend = () => {this_.model.speech_started=false}

        this.recognition.onstart = function(){
            this_.buttonEl.onclick = () => {this_.recognition.end()}
            this_.buttonEl.innerHTML = iconStarted;
            this_.buttonEl.setAttribute("title", titleStarted);
            this_.model.started = true;
        }
        this.recognition.onend = function(){
            this_.buttonEl.onclick = () => {this_.recognition.start()}
            this_.buttonEl.innerHTML = iconNotStarted;
            this_.buttonEl.setAttribute("title", titleNotStarted);
            this_.model.started = false;

        }
    }

    connect_signals(): void {
        super.connect_signals()

        this.connect(this.model.properties.stops.change, () => {this.recognition.stops=this.model.stops;console.log("stops");})
        this.connect(this.model.properties.aborts.change, () => {this.recognition.aborts=this.model.aborts;console.log("aborts");})
        this.connect(this.model.properties.grammars.change, () => {this.setGrammars})
        this.connect(this.model.properties.lang.change, () => {this.recognition.lang=this.model.lang;console.log("lang");})
        this.connect(this.model.properties.continous.change, () => {this.recognition.continous=this.model.continous;console.log("continous");})
        this.connect(this.model.properties.interim_results.change, () => {this.recognition.interim_results=this.model.interim_results;console.log("interim_results");})
        this.connect(this.model.properties.max_alternatives.change, () => {this.recognition.max_alternatives=this.model.max_alternatives;console.log("max_alternatives");})
        this.connect(this.model.properties.service_uri.change, () => {this.recognition.service_uri=this.model.service_uri;console.log("service_uri");})
        this.connect(this.model.properties.button_type.change, () => {this.buttonEl.className=`bk bk-btn bk-btn-${this.model.button_type}`})
    }

    render(): void {
        super.render()
        this.buttonEl = htmlToElement(`<button class="bk bk-btn bk-btn-${this.model.button_type}" type="button" title="${titleNotStarted}"></button>`)
        this.buttonEl.innerHTML = iconNotStarted
        this.buttonEl.onclick = () => {this.recognition.start()}
        this.el.appendChild(this.buttonEl)
    }

    setGrammars(): void {
        this.recognition.grammars=deserializeGrammars(this.model.grammars);
    }
}

export namespace SpeechToText {
  export type Attrs = p.AttrsOf<Props>
  export type Props = HTMLBox.Props & {
    starts: p.Property<number>
    stops: p.Property<number>
    aborts: p.Property<any>

    grammars: p.Property<any[]>
    lang: p.Property<string>
    continous: p.Property<boolean>
    interim_results: p.Property<boolean>
    max_alternatives: p.Property<number>
    service_uri: p.Property<string>
    started: p.Property<boolean>
    audio_started: p.Property<boolean>
    sound_started: p.Property<boolean>
    speech_started: p.Property<boolean>
    button_type: p.Property<string>
    results: p.Property<any[]>
  }
}

export interface SpeechToText extends SpeechToText.Attrs {}

export class SpeechToText extends HTMLBox {
  properties: SpeechToText.Props

  constructor(attrs?: Partial<SpeechToText.Attrs>) {
    super(attrs)
  }

  static __module__ = "panel.models.speech_to_text"

  static init_SpeechToText(): void {
    this.prototype.default_view = SpeechToTextView

    this.define<SpeechToText.Props>({
        starts: [ p.Number, 0     ],
        stops: [ p.Number, 0     ],
        aborts: [ p.Number, 0     ],

        grammars: [p.Array, []],
        lang: [p.String, ],
        continous: [ p.Boolean,   false ],
        interim_results: [ p.Boolean,   false ],
        max_alternatives: [ p.Number,   1 ],
        service_uri: [p.String, ],
        started: [ p.Boolean,   false ],
        audio_started: [ p.Boolean,   false ],
        sound_started: [ p.Boolean,   false ],
        speech_started: [ p.Boolean,   false ],
        button_type: [p.String, 'light'],
        results: [ p.Array, []],
    })
  }
}
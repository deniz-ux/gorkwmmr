import { HTMLBox, HTMLBoxView } from "models/layouts/html_box"

import { div } from "core/dom"
import * as p from "core/properties"

export class LocationView extends HTMLBoxView {
    model: Location

    connect_signals(): void {
        console.info("connect_signals");
        super.connect_signals();

        this.render();

        this.connect(this.model.properties.href.change, () => this.update_href());

        this.connect(this.model.properties.hostname.change, () => this.update_part_by_part());
        this.connect(this.model.properties.pathname.change, () => this.update_part_by_part());
        this.connect(this.model.properties.protocol.change, () => this.update_part_by_part());
        this.connect(this.model.properties.port.change, () => this.update_part_by_part());
        this.connect(this.model.properties.search.change, () => this.update_part_by_part());
        this.connect(this.model.properties.hash_.change, () => this.update_part_by_part());
    }

    update_href(): void {
        console.log("update_href")
        if (this.model.refresh) {
            window.history.pushState({}, '', this.model.href);
        } else {
            window.location.href = this.model.href;
        }

        this.model.hostname = window.location.hostname;
        this.model.pathname = window.location.pathname;
        this.model.protocol = window.location.protocol;
        this.model.port = window.location.port;
        this.model.search = window.location.search;
        this.model.hash_ = window.location.hash;
    }
    update_part_by_part(): void {
        console.log("update_by_part")
        if (this.model.refresh) {
            window.history.pushState(
                {},
                '',
                `${this.model.pathname}:${this.model.port}${this.model.search}${this.model.hash_}`
            );
        } else {
            window.location.hostname = this.model.hostname;
            window.location.pathname = this.model.pathname;
            window.location.protocol = this.model.protocol;
            window.location.port = this.model.port;
            window.location.search = this.model.search;
            window.location.hash = this.model.hash_;
        }

        this.model.href = window.location.href;
    }

    render(): void {
        // Todo: remove content. Here for manual testing
        console.info("render");
        super.render()

        var myString = `
        ${this.model.href}
        ${this.model.hostname}
        ${this.model.pathname}
        ${this.model.protocol}
        ${this.model.port}
        ${this.model.search}
        ${this.model.hash_}
        ${this.model.refresh}
        `;

        this.el.appendChild(div({
            style: {
                padding: '2px',
                color: '#b88d8e',
                backgroundColor: '#2a3153',
            },
        }, myString))
    }
}

export namespace Location {
    export type Attrs = p.AttrsOf<Props>
    export type Props = HTMLBox.Props & {
        href: p.Property<string>
        hostname: p.Property<string>
        pathname: p.Property<string>
        protocol: p.Property<string>
        port: p.Property<string>
        search: p.Property<string>
        hash_: p.Property<string>
        refresh: p.Property<boolean>
    }
}

export interface Location extends Location.Attrs { }

export class Location extends HTMLBox {
    properties: Location.Props

    constructor(attrs?: Partial<Location.Attrs>) {
        super(attrs)
    }

    static init_Location(): void {
        this.prototype.default_view = LocationView;

        this.define<Location.Props>({
            href: [p.String, window.location.href],
            hostname: [p.String, window.location.hostname],
            pathname: [p.String, window.location.pathname],
            protocol: [p.String, window.location.protocol],
            port: [p.String, window.location.port],
            search: [p.String, window.location.search],
            hash_: [p.String, window.location.hash],
            refresh: [p.Boolean, true],
        })
    }
}

import { Network } from "vis";

// Extensions.

export interface VisBody {
    data: {
        nodes: vis.DataSet<vis.Node>;
        edges: vis.DataSet<vis.Edge>;
    }
}

export interface VisNet extends Network {
    body: VisBody;

    getOptions: () => any;
}

// Types.

export type Optional<T> = T | null;

export type Undefinable<T> = T | undefined;

export type Ts_Action = "pause" | "interrupt" | "reset" | "delay";

export type Ts_Edge = {
    "from": Optional<Py_Symbol>,
    "to": Optional<Py_Symbol>,
}

export type Ts_Add = Record<number, Py_Graph>;
export type Ts_Mov = Record<number, Ts_Edge>;
export type Ts_Del = Ts_Add;

export type Ts_Update = {
    "addu": Ts_Add,
    "movu": Ts_Mov,
    "delu": Ts_Del,
}

export type Py_Symbol = {
    "label": string,
    "id": string,
    "kind": string,
}

export type Py_Edge = {
    "from": string,
    "to": string,
}

export type Py_Graph = {
    "nodes": Py_Symbol[],
    "edges": Py_Edge[],
}

export type Py_TrailLayer = {
    "graph": Py_Graph,
    "state": Py_Symbol,
    "label": string,
}

export type Py_TrailState = Py_TrailLayer[];

export type Py_Data = {
    "results": Py_TrailState[][],
    "response": string[],
    "completed": boolean,
}

export type Py_Setting = {
    "paused": boolean,
    "interrupted": boolean,
    "reset": boolean,
}

export type Py_Recieve = {
    data: Py_Data,
    setting: Py_Setting,
}

export type Ts_Send = {
    "status": "success",
    "state": Py_Data,
}

export type Ts_State = {
    response: Py_Recieve,
    frame: number,
    fetch: boolean,
    interfaces: Ts_Interface[],
    networks: Ts_Network[],
    active: HTMLElement[][],
}

export type Ts_Network = {
    front: Optional<Network>,
    sides: Network[],
}


export type Ts_Interface = {
    front: HTMLElement,
    sides: HTMLElement,
}
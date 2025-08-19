import { Network } from "vis";

export { Network };

// Interfaces.
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

// Types
export type LTId = string;

export type Optional<T> = T | null;

export type LTAction = "pause" | "interrupt" | "reset" | "delay";

export type LTNode = {
    "id": LTId,
    "label": string,
    "color": string,
};

export type LTEdge = {
    "from": LTId,
    "to": LTId,
};

export type LTGraph = {
    "nodes": LTNode[],
    "edges": LTEdge[],
};

export type LTUpdate = {
    "addu": Record<number, LTGraph>,
    "movu": Record<number, LTEdge>,
    "delu": Record<number, LTGraph>,
};

export type LTData = {
    "updates": LTUpdate[][],
    "rollbacks": LTUpdate[][],
    "previews": LTId[][],
    "response": string[],
    "completed": boolean,
};

export type LTSetting = {
    "paused": boolean,
    "interrupted": boolean,
    "reset": boolean,
    "delay": number,
    "run": number,
};

export type LTFetch = {
    data: LTData,
    setting: LTSetting,
};

export type LTSend = {
    "status": "success",
    "state": LTData,
}

export type LTState = {
    response: LTFetch,
    frame: number,
    delay: number,
    fetch: boolean,
    interfaces: LTInterface[],
    networks: LTNetwork[],
    active: HTMLElement[][],
}

export type LTNetwork = {
    front: Optional<Network>,
    sides: Network[],
}

export type LTNetworkA = {
    front: Network[],
    sides: Network[][],
}

export type LTInterface = {
    front: HTMLElement,
    sides: HTMLElement,
}
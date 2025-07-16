import { LTFetch, LTState, LTNetwork, LTNetworkA } from './types';
import { getRequiredElement, updateControlButtons } from './helpers';
import { DOM, addEventListeners } from './interface';
import { updateFrame, updateGraphs } from './render';

async function loadGraphs(state: LTState): Promise<void> {
    if (!state.fetch) null;

    try {
        const response = await fetch("/graph");
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

        const content: LTFetch = await response.json();

        if (JSON.stringify(content.data.updates) !== JSON.stringify(state?.response?.data?.updates)) {
            updateFrame(DOM, state, content.data);

            // [NOTE] Deepcopies are known to be very expensive.
            state.response.data = content.data;
        }

        const isPaused = content.setting.paused;
        const isInterrupted = content.setting.interrupted;
        const isComplete = state.response.data.completed;

        const total = content.data.updates.length;

        updateControlButtons(DOM, state.frame, total,
            isPaused, isInterrupted, isComplete);

        if (isComplete || isInterrupted) {
            state.fetch = false;
            if (isInterrupted) {
                DOM.display.status.innerHTML =
                    `Simulation interrupted. Displaying Subgraph ${total} of ${total}`;
            } else if (isComplete) {
                DOM.display.status.innerHTML =
                    `Simulation complete. Displaying Subgraph ${total} of ${total}`;
            }
        }

        loadGraphs(state);
    }
    catch (error) {
        console.error("Error loading graphs:", error);
        document.getElementById('status')!.innerHTML = "Failed to load graphs. Check server connection.";
    }
}

function main() {
    // Initialize.
    // const network: LTNetwork = { front: null, sides: [] };
    // const networks: LTNetworkA = { front: [], sides: [] };

    const INITIAL_STATE: LTState = {
        response: {
            data: {
                "updates": [],
                "rollbacks": [],
                "previews": [],
                "response": [],
                "completed": false,
            }
            , setting: {
                "paused": false,
                "interrupted": false,
                "reset": false,
                "delay": 1000,
            }
        }, interfaces: [], networks: [], frame: 0, delay: 1000, active: [], fetch: true
    };

    // INITIAL_STATE.interfaces.push({
    //     front: getRequiredElement<HTMLElement>('graph-container_0'),
    //     sides: getRequiredElement<HTMLElement>('sidebar-items_0'),
    // })

    // INITIAL_STATE.networks.push({
    //     front: null,
    //     sides: [],
    // });

    INITIAL_STATE.active.push([])

    addEventListeners(DOM, INITIAL_STATE.networks, INITIAL_STATE, updateGraphs);

    loadGraphs(INITIAL_STATE);
}

main();
import { LTFetch, LTState, LTNetwork } from './types';
import { updateControlButtons } from './helpers';
import { DOM, addEventListeners } from './interface';
import { updateFrame, updateGraphs } from './render';

async function loadGraphs(network: LTNetwork, state: LTState): Promise<void> {
    if (!state.fetch) null;

    try {
        const response = await fetch("/graph");
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

        const content: LTFetch = await response.json();

        if (JSON.stringify(content.data.updates) !== JSON.stringify(state?.response?.data?.updates)) {
            await updateFrame(DOM, network, state, content.data);

            // [NOTE] Deepcopies are known to be very expensive.
            state.response.data = content.data;
        }

        const isPaused = content.setting.paused;
        const isInterrupted = content.setting.interrupted;
        const isComplete = state.response.data.completed;

        console.log(isComplete);

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

        loadGraphs(network, state);
    }
    catch (error) {
        console.error("Error loading graphs:", error);
        document.getElementById('status')!.innerHTML = "Failed to load graphs. Check server connection.";
    }
}

async function main() {
    // Initialize.
    const network: LTNetwork = { front: null, sides: [] };

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
        }, frame: 0, delay: 1000, active: null, fetch: true
    };

    addEventListeners(DOM, network, INITIAL_STATE, updateGraphs);

    await loadGraphs(network, INITIAL_STATE);
}

main();
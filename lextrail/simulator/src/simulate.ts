import { Py_Recieve, Ts_State } from './types';
import { updateControlButtons, getRunIndex } from './helpers';
import { updateFrame, updateGraphs } from './render';
import { DOM, addEventListeners } from './interface';

async function loadGraphs(state: Ts_State): Promise<void> {
    if (!state.fetch) null;

    try {
        const response = await fetch("/graph");
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

        const content: Py_Recieve = await response.json();

        const isPaused = content.setting.paused;
        const isInterrupted = content.setting.interrupted;
        const isComplete = content.data.completed;

        const total = content.data.results.length;

        if (
            // [NOTE] Each run has an assigned ID, during a reset, the ID is incremented. No update
            // is issued when there is a mismatch between Python and TypeScript.
            content.setting.run === state.response.setting.run &&
            JSON.stringify(content.data.results) !== JSON.stringify(state?.response?.data?.results)) {
            updateFrame(DOM, state, content.data);

            if (isComplete)
                DOM.display.status.innerHTML =
                    `Simulation complete. Displaying frame ${total} of ${total}`;
        }

        updateControlButtons(DOM, state.frame, total,
            isPaused, isInterrupted, isComplete);

        DOM.display.frameCounter.textContent = `Frame ${state.frame}/${total}`;

        // Update LLM response (fragmented strings allows simple transitions to previous frames).
        DOM.display.llmResponse.value = state.response.data.response.slice(0, state.frame).join('') || "No response available";

        if (isInterrupted) {
            state.fetch = false;
            DOM.display.status.innerHTML =
                `Simulation interrupted. Displaying frame ${total} of ${total}`;
        }

        loadGraphs(state);
    }
    catch (error) {
        console.error("Error loading graphs:", error);
        document.getElementById('status')!.innerHTML = "Failed to load graphs. Check server connection.";
    }
}

async function main() {
    const INITIAL_STATE: Ts_State = {
        response: {
            data: {
                "results": [],
                "response": [],
                "completed": false,
            },
            setting: {
                "paused": false,
                "interrupted": false,
                "reset": false,
                "delay": 1000,
                "run": await getRunIndex(),
            }
        }, interfaces: [], networks: [], frame: 0, delay: 1000, active: [], fetch: true
    };

    INITIAL_STATE.active.push([])

    addEventListeners(DOM, INITIAL_STATE, updateGraphs);

    loadGraphs(INITIAL_STATE);
}

main();
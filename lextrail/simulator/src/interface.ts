import { getRequiredElement, sendControlCommand, updateGraphFontColors } from './helpers';
import { updateLayout, removeNetwork, removeInterface } from './layout';
import { createUpdate } from './render';
import {
	Optional,
	Ts_Update, Ts_State
} from './types';

export type DOM = {
	root: HTMLElement,

	buttons: {
		btnPrev: HTMLButtonElement;
		btnNext: HTMLButtonElement;
		btnPause: HTMLButtonElement;
		btnInterrupt: HTMLButtonElement;
		btnReset: HTMLButtonElement;
		btnDelay: HTMLButtonElement;
	},

	inputs: {
		delayInput: HTMLInputElement;
		delaySlider: HTMLInputElement;
	},

	theme: {
		themeToggle: HTMLElement;
		icon: Optional<HTMLElement>;
	},

	display: {
		frameCounter: HTMLElement;
		status: HTMLElement;
		currentSidebar: HTMLElement;
		currentDisplay: HTMLElement;
		llmResponse: HTMLTextAreaElement;
	},
};

type LTCall = (state: Ts_State, updates: Ts_Update[]) => Promise<void>;

export const DOM: DOM = {
	root: document.documentElement,

	buttons: {
		btnPrev: getRequiredElement<HTMLButtonElement>('btn-prev'),
		btnNext: getRequiredElement<HTMLButtonElement>('btn-next'),
		btnPause: getRequiredElement<HTMLButtonElement>('btn-pause'),
		btnInterrupt: getRequiredElement<HTMLButtonElement>('btn-interrupt'),
		btnReset: getRequiredElement<HTMLButtonElement>('btn-reset'),
		btnDelay: getRequiredElement<HTMLButtonElement>('btn-delay'),
	},

	inputs: {
		delayInput: getRequiredElement<HTMLInputElement>('delay-input'),
		delaySlider: getRequiredElement<HTMLInputElement>('delay-slider'),
	},

	theme: {
		themeToggle: getRequiredElement('theme-toggle'),
		icon: null,
	},

	display: {
		frameCounter: getRequiredElement<HTMLElement>('frame-counter'),
		status: getRequiredElement<HTMLElement>('status'),
		currentSidebar: getRequiredElement<HTMLElement>('current-sidebar'),
		currentDisplay: getRequiredElement<HTMLElement>('current-display'),
		llmResponse: getRequiredElement<HTMLTextAreaElement>('llm-response'),
	},
}

// Set the toggle icon.
DOM.theme.icon = DOM.theme.themeToggle.querySelector('i');

export async function addEventListeners(DOM: DOM, state: Ts_State, updateGraphs: LTCall) {
	DOM.buttons.btnPrev.addEventListener('click', () => {
		const prevResults = state.response.data.results[state.frame - 1];
		const nextResults = state.response.data.results[state.frame - 2];

		const updates = nextResults.map((nextStates, i) =>
			createUpdate(prevResults[i] ?? prevResults[0], nextStates)
		);

		const prevLength = state.networks.length;
		const nextLength = nextResults.length;

		if (prevLength === 0) {
			throw Error("Cannot proceed from an empty state.");
		} else {
			updateLayout(DOM, state, nextLength);
		}

		updateGraphs(state, updates);

		// Update frame.
		state.frame -= 1;

		// Update counter.
		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.response.data.results.length}`;

	});

	DOM.buttons.btnNext.addEventListener('click', () => {
		const prevResults = state.response.data.results[state.frame - 1];
		const nextResults = state.response.data.results[state.frame];

		const updates = nextResults.map((nextStates, i) =>
			createUpdate(prevResults[i] ?? prevResults[0], nextStates)
		);

		const nextLength = nextResults.length;
		const prevLength = state.networks.length;

		if (prevLength === 0) {
			throw Error("Cannot proceed from an empty state.");
		} else {
			updateLayout(DOM, state, nextLength);
		}

		updateGraphs(state, updates);

		// Update frame.
		state.frame += 1;

		// Update counter.
		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.response.data.results.length}`;
	});

	DOM.buttons.btnPause.addEventListener('click', () => {
		sendControlCommand('pause');
	});

	DOM.buttons.btnInterrupt.addEventListener('click', () => {
		if (confirm('Are you sure you want to interrupt the simulation? This cannot be undone.')) {
			sendControlCommand('interrupt');
		}
	});

	DOM.buttons.btnReset.addEventListener('click', () => {
		if (confirm('Are you sure you want to reset the simulation?')) {
			sendControlCommand('reset');

			// Increments a run state to avoid updates until Python sends the reset data.
			state.response.setting.run += 1;

			// Reset status.
			DOM.display.status.innerHTML = "Loading graphs from server...";

			// Reset state.
			state.fetch = true;
			state.frame = 0;

			const size = state.networks.length;

			// Clear networks and interfaces.
			for (let i = 0; i < size; i++) {
				removeNetwork(state, 0)
			}

			if (state.networks.length !== 0) {
				throw Error("Networks were not reset.")
			}

			for (let i = 0; i < size; i++) {
				removeInterface(DOM, state, 0)
			}

			if (state.interfaces.length !== 0) {
				throw Error("Interfaces were not reset.")
			}
		}
	});

	DOM.buttons.btnDelay.addEventListener('click', () => {
		let delay = state.delay
		delay = parseInt(DOM.inputs.delayInput.value);
		if (!isNaN(delay) && delay >= 0) {
			sendControlCommand('delay', { rate: delay / 1000 });
		}
	});

	// Inputs.
	DOM.inputs.delaySlider.addEventListener('input', () => {
		DOM.inputs.delayInput.value = DOM.inputs.delaySlider.value;
	});

	DOM.inputs.delayInput.addEventListener('input', () => {
		DOM.inputs.delaySlider.value = DOM.inputs.delayInput.value;
	});

	// Theme.
	DOM.theme.themeToggle.addEventListener('click', () => {
		if (DOM.root.classList.contains('light-mode')) {
			DOM.root.classList.remove('light-mode');
			if (DOM.theme.icon) DOM.theme.icon.className = 'fas fa-sun';
			localStorage.setItem('theme', 'dark');
		} else {
			DOM.root.classList.add('light-mode');
			if (DOM.theme.icon) DOM.theme.icon.className = 'fas fa-moon';
			localStorage.setItem('theme', 'light');
		}
		updateGraphFontColors(state.networks, DOM.root)
	});

}


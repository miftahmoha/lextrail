import { getRequiredElement, sendControlCommand, updateFramesButtons, updateGraphFontColors } from './helpers';
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
		btnPause: HTMLButtonElement;
		btnNext: HTMLButtonElement;
		btnFirst: HTMLButtonElement;
		btnLast: HTMLButtonElement;
		btnInterrupt: HTMLButtonElement;
		btnReset: HTMLButtonElement;
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
		btnPause: getRequiredElement<HTMLButtonElement>('btn-pause'),
		btnNext: getRequiredElement<HTMLButtonElement>('btn-next'),
		btnFirst: getRequiredElement<HTMLButtonElement>('btn-first'),
		btnLast: getRequiredElement<HTMLButtonElement>('btn-last'),
		btnInterrupt: getRequiredElement<HTMLButtonElement>('btn-interrupt'),
		btnReset: getRequiredElement<HTMLButtonElement>('btn-reset'),
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
		const totalFrames = state.response.data.results.length;

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

		state.frame -= 1;

		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${totalFrames}`;

		updateFramesButtons(DOM, state.frame, totalFrames)
	});

	DOM.buttons.btnNext.addEventListener('click', () => {
		const totalFrames = state.response.data.results.length;

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

		state.frame += 1;

		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${totalFrames}`;

		updateFramesButtons(DOM, state.frame, totalFrames)
	});

	DOM.buttons.btnFirst.addEventListener('click', () => {
		const totalFrames = state.response.data.results.length;

		const prevResults = state.response.data.results[state.frame - 1];
		const nextResults = state.response.data.results[0];

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

		state.frame = 1;

		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${totalFrames}`;

		updateFramesButtons(DOM, state.frame, totalFrames)
	});

	DOM.buttons.btnLast.addEventListener('click', () => {
		const totalFrames = state.response.data.results.length;

		const prevResults = state.response.data.results[state.frame - 1];
		const nextResults = state.response.data.results[totalFrames - 1];

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

		state.frame = totalFrames;

		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${totalFrames}`;

		updateFramesButtons(DOM, state.frame, totalFrames)
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

			state.frame = 0;

			// Allows reset when incoming data matches last sent data.
			state.response.data.completed = false;

			DOM.display.status.innerHTML = "Loading graphs from server...";

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


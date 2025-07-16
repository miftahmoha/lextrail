import { Optional, LTNetwork, LTId, LTState, LTUpdate, LTData } from './types';
import { getRequiredElement, sendControlCommand, updateGraphFontColors } from './helpers';

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
		currentGraph: HTMLElement;
		llmResponse: HTMLTextAreaElement;
	},
};

type LTCall = (state: LTState, updates: LTUpdate[], previews: string[]) => void;

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
		currentGraph: getRequiredElement<HTMLElement>('current-graph'),
		llmResponse: getRequiredElement<HTMLTextAreaElement>('llm-response'),
	},
}

// Set the toggle icon.
DOM.theme.icon = DOM.theme.themeToggle.querySelector('i');

export function addEventListeners(DOM: DOM, network: LTNetwork[],
	state: LTState, updateGraphs: LTCall) {
	// DOM.buttons.btnPrev.addEventListener('click', () => {
	// 	const rollbacks = state.response.data.rollbacks;
	// 	if (rollbacks.length <= 0) {
	// 		console.error("No graph history found.");
	// 		return;
	// 	}

	// 	// Will transition to the previous frame.
	// 	const previous = rollbacks[state.frame - 1]
	// 	if (!previous) {
	// 		console.error("Previous frame is not found.");
	// 		return;
	// 	}

	// 	updateGraphs(state, previous, []);

	// 	// Update state.
	// 	state.frame -= 1;

	// 	// Update counter.
	// 	DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.response.data.rollbacks.length}`;
	// });

	// DOM.buttons.btnNext.addEventListener('click', () => {
	// 	const updates = state.response.data.updates;
	// 	if (updates.length <= 0) {
	// 		console.error("No graph history found.");
	// 		return;
	// 	}

	// 	// Will transition to the next frame.
	// 	const next = state.response.data.updates[state.frame]
	// 	if (!next) {
	// 		console.error("Next frame is not found.");
	// 		return;
	// 	}

	// 	updateGraphs(network, state, next, []);

	// 	// Update state.
	// 	state.frame += 1;

	// 	// Update counter.
	// 	DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.response.data.updates.length}`;
	// });

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
			// Reset state.
			state.frame = 0;
			state.fetch = true;
			// [TODO?] Should destroy the networks and interface divs?
			state.interfaces = [];

			document.querySelectorAll('.current-subgraph-container').forEach(container => {
				container.remove();
			});
			state.networks = [];
			document.querySelectorAll('.sidebar-items').forEach(container => {
				container.remove();
			});
			// Clear the sidebar.
			document.querySelectorAll('.sidebar-item').forEach(el => {
				el.remove();
			});

			sendControlCommand('reset');
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
		updateGraphFontColors(network, DOM.root)
	});

}


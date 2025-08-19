import { VisNet, LTNetwork, LTUpdate, LTState, Optional } from './types';
import { getRequiredElement, sendControlCommand, updateGraphFontColors } from './helpers';
import { updateLayout, clonePlaceholders, removePlaceholders, removeNetwork, removeInterface } from './layout';
import { moveHighlight } from './render';

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

type LTCall = (state: LTState, updates: LTUpdate[], previews: string[], idx: number) => Promise<void>;

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

export async function addEventListeners(DOM: DOM, state: LTState, updateGraphs: LTCall) {
	DOM.buttons.btnPrev.addEventListener('click', async () => {
		// Update state.
		state.frame -= 1;

		const rollbacks = state.response.data.rollbacks;
		if (rollbacks.length <= 0) {
			console.error("No graph history found.");
			return;
		}

		// Will transition to the previous frame.
		const current = rollbacks[state.frame]
		if (!current) {
			console.error("Previous frame is not found.");
			return;
		}

		function cleanLayout(DOM: DOM, state: LTState, update: LTUpdate[]) {
			// [TODO] `pop` extracts the highest indexed key.
			const toIds = update.map(u => Object.values(u.movu).pop()?.to);
			if (!toIds.every(Boolean)) {
				throw Error("Ambiguous nodes were not found.");
			}

			// Check if it's a convergence phase, opposite of an ambiguity where 
			// (ambiguous) nodes converge to the same root node.
			const sharedIds = new Set(toIds).size;
			if (sharedIds === 1) {
				// Remove the excess graphs.
				for (let indexOut = 1; indexOut < update.length; indexOut++) removePlaceholders(DOM, state, indexOut);
			}
			else if (sharedIds !== toIds.length) {
				throw Error("Ambiguous nodes with different content found.");
			}
		}

		function correctHighlights(state: LTState, update: LTUpdate[]) {
			// `pop` extracts the highest indexed key.
			const fromIds = update.map(u => Object.values(u.movu).pop()?.from);
			if (!fromIds.every(Boolean)) {
				throw Error("Ambiguous nodes were not found.");
			}

			// Get the current highlighted node, then move it to each node in `fromIds`. 
			// [NOTE] The networks are copies of each others.
			const graph = state.networks[0].sides.at(-1) as VisNet;

			const currentHighlight = graph.body.data.nodes.get({
				filter: (node) => {
					if (!node.color || typeof node.color === 'string') return false;
					return node.color.background === '#06b6d4' && node.color.border === '#06b6d4';
				}
			});

			// Since every other graph is a clone, the goal is to move the hightlight from the id
			// at index 0, to index 0 at 0, index 0 to index 1, at 1 ect..
			for (let i = 0; i < fromIds.length; i++) {
				const lastNetwork = state.networks[i].sides.at(-1);
				if (!lastNetwork) {
					throw Error("Ambiguous network was not found.")
				}

				// [NOTE] Since networks at the front are references of the sides,
				// then moving at the sides is enough.
				moveHighlight(lastNetwork, currentHighlight[0].id as string, fromIds[i]!);
			}
		}

		// Step (1) is about to rollback, then clean the layout if there is a convergence.
		await updateGraphs(state, current, [], 4);

		// [NOTE] Inversing a cloning step will turn into a convergence, 
		// ambiguous graphs will converge to the same root node. 
		// [NOTE] Duplicates then need to be eliminated.
		if (state.networks.length > 1) {
			cleanLayout(DOM, state, current)
		}

		// Step (2) is about to pre-clone the graphs for the next update if there is an ambiguity.
		// [NOTE] `current` here expresses the current update to go to the previous frame,
		// rolling back in the context of ambiguity can be more challenging to grasp since
		// we'll need `previous` as well which is the previous update to go the previous² frame.
		const previous = rollbacks[state.frame - 1];
		if (!previous) {
			console.error("Previous frame is not found.");
			return;
		}

		const currLength = state.networks.length;
		const nextLength = previous.length;

		const offset = nextLength - currLength;
		if (currLength === 0) {
			throw Error("Cannot revert from an empty state.");
		} else if (offset > 0) {
			// [NOTE] If we get to a positive offset with an ambiguous state, it means that excess
			// graphs didn't get cleaned at some point.
			if (currLength > 1) {
				throw Error("Layout was not cleaned properly.");
			}

			// [NOTE] Inversing a choice step will turn into a clone, but different,
			// the clone will be on index `0` with a correction.
			Array.from({ length: offset }).forEach(() => clonePlaceholders(DOM, state, 0));

			// [NOTE] A correction means that after cloning the layout, we'll need to move the
			// highlight to the unchosen ambiguous nodes.
			correctHighlights(state, previous);
		}

		// Update counter.
		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.response.data.rollbacks.length}`;
	});

	DOM.buttons.btnNext.addEventListener('click', () => {
		const updates = state.response.data.updates;
		if (updates.length <= 0) {
			console.error("No graph history found.");
			return;
		}

		// Will transition to the next frame.
		const next = state.response.data.updates[state.frame]
		if (!next) {
			console.error("Next frame is not found.");
			return;
		}

		const nextLength = next.length;
		const currLength = state.networks.length;

		if (currLength === 0) {
			throw Error("Cannot proceed from an empty state.");
		} else {
			// If `(currLength - prevLength) != 0` means either (1) we've got an ambiguity and we've 
			// got to render every possible graph, or (2) we've come from one and we've got to render the chosen graph.
			// If `(currLength - prevLength) == 0` means we've got a (chosen) subgraph of ambiguities
			// from the original graphs.
			updateLayout(DOM, state, currLength, next);
		}

		updateGraphs(state, next, [], 4);

		// Update state.
		state.frame += 1;

		// Update counter.
		DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.response.data.updates.length}`;
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

			// Clear networks and interfaces.
			for (let i = 0; i < state.networks.length; i++) {
				removeNetwork(state, i)
			}

			if (state.networks.length !== 0) {
				throw Error("Networks were not reset.")
			}

			for (let i = 0; i < state.interfaces.length; i++) {
				removeInterface(DOM, state, i)
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


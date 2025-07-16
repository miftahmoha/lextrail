import { VisNet, LTAction, LTNetwork, LTNetworkA } from './types';
import { DOM } from './interface'
import { Network, Options } from "vis";

export function getRequiredElement<T extends HTMLElement>(id: string): T {
	const element = document.getElementById(id) as T | null;
	if (!element) {
		throw new Error(`Required DOM element '${id}' not found`);;
	}
	return element;
}

export function updatePlayPauseButton(DOM: DOM, isPaused: boolean): void {
	const icon = DOM.buttons.btnPause.querySelector('i');
	if (!icon) {
		console.error("Pause/Resume icon not found.");
		return;
	}

	if (isPaused) {
		icon.className = 'fas fa-play';
	} else {
		icon.className = 'fas fa-pause';
	}
}

export function updateControlButtons(DOM: DOM, currentFrame: number, totalFrames: number,
	isPaused: boolean, isInterrupted: boolean, isComplete: boolean) {
	DOM.buttons.btnPause.disabled = isInterrupted || isComplete;
	updatePlayPauseButton(DOM, isPaused);
	DOM.buttons.btnPrev.disabled = currentFrame <= 1 || isInterrupted;
	DOM.buttons.btnNext.disabled = currentFrame >= totalFrames || isInterrupted;
	DOM.buttons.btnInterrupt.disabled = isInterrupted || isComplete;
	DOM.buttons.btnDelay.disabled = isInterrupted || isComplete;
	DOM.inputs.delayInput.disabled = isInterrupted || isComplete;
}

export function updateGraphFontColors(networks: LTNetwork[], root: HTMLElement): void {
	const color = root.classList.contains('light-mode') ? '#000000' : '#ffffff';

	const sections = networks.length;

	// Update thumbnail graphs.
	for (let i: number = 0; i < sections; i++) {
		networks[i].sides.forEach((graph) => {
			if (graph) {
				const nodes = (graph as VisNet).body.data.nodes;
				nodes.forEach(node => {
					nodes.update({
						id: node.id,
						font: {
							color: color
						}
					});
				});
			}
		});


		// Update main graph.
		if (networks[i].front) {
			const nodes = (networks[i].front as VisNet).body.data.nodes;
			nodes.forEach(node => {
				nodes.update({
					id: node.id,
					font: {
						color: color
					}
				});
			});
		}
	}
}


// Sending data to the server.
export function sendControlCommand(action: LTAction, extraData: { rate?: number } = {}) {
	const data = {
		action: action,
		...extraData
	};
	fetch('/control', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(data),
	})
		.then(response => response.json())
		.then(data => {
			console.log('Control command response:', data);
		})
		.catch(error => {
			console.error('Error sending control command:', error);
		});
}

export function cloneNetwork(sourceNetwork: Network, targetContainer: HTMLElement, options: Options): Network {
	const graphDataClone = {
		nodes: (sourceNetwork as VisNet).body.data.nodes.get(),
		edges: (sourceNetwork as VisNet).body.data.edges.get(),
	} as any;

	return new Network(targetContainer, structuredClone(graphDataClone), options);
}

export function cloneNetwork_(sourceNetwork: Network, targetContainer: HTMLElement, options: Options): Network {
	const graphDataClone = {
		nodes: (sourceNetwork as VisNet).body.data.nodes,
		edges: (sourceNetwork as VisNet).body.data.edges,
	} as any;

	return new Network(targetContainer, graphDataClone, options);
}

export function cloneContainer(sourceContainer: HTMLElement): HTMLElement {
	const clonedContainer = sourceContainer.cloneNode(true) as HTMLElement;

	function updateElementIds(element: HTMLElement) {
		if (element.id) {
			element.id = getNextAvailableId(element.id);
		}

		// if (element.tagName === 'LABEL' && element.hasAttribute('for')) {
		// 	const forValue = element.getAttribute('for');
		// 	if (forValue) {
		// 		element.setAttribute('for', getNextAvailableId(forValue, indicesToAvoid));
		// 	}
		// }

		const children = Array.from(element.children) as HTMLElement[];
		children.forEach((child: HTMLElement) => {
			updateElementIds(child);
		});
	}

	function getNextAvailableId(currentId: string): string {
		// Extract the base name and current number from SOME_NAME#X format
		const match = currentId.match(/^(.+)_(\d+)$/);
		if (!match) {
			throw new Error(`Element ID "${currentId}" does not follow the required SOME_NAME_X format`);
		}

		const baseName = match[1];
		const currentNumber = parseInt(match[2], 10);

		let nextNumber = currentNumber + 1;
		// [NOTE] Avoids cloning into an existent object.
		while (document.querySelector(`#${baseName}_${nextNumber}`)) {
			nextNumber++;
		}

		return `${baseName}_${nextNumber}`;
	}

	updateElementIds(clonedContainer);
	return clonedContainer;
}
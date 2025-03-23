import { create } from "zustand";

const useSourcesStore = create(set => ({
	sources: [
		//{
		//	id: 1,
		//	name: "slides 1",
		//	summary: "This is a summary of the source",
		//	selected: true,
		//},
		//{
		//	id: 2,
		//	name: "slides 2",
		//	summary: "This is a summary of the source",
		//	selected: true,
		//},
		//{
		//	id: 3,
		//	name: "lecture #1 recording",
		//	summary: "This is a summary of the source",
		//	selected: true,
		//},
		//{
		//	id: 4,
		//	name: "lecture #2 recording",
		//	summary: "This is a summary of the source",
		//	selected: true,
		//},
	],
	setSources: sources => set({ sources }),
	setSourceChecked: (id, checked) =>
		set(state => ({
			sources: state.sources.map(source =>
				source.id === id ? { ...source, selected: checked } : source,
			),
		})),
	renameSource: async (id, name) => {
		set(state => ({
			sources: state.sources.map(source =>
				source.id === id ? { ...source, name } : source,
			),
		}));
	},
	deleteSource: async id => {
		set(state => ({
			sources: state.sources.filter(source => source.id !== id),
		}));
	},
	addSource: async source => {
		set(state => ({
			sources: [
				...state.sources,
				{
					id: Math.max(...state.sources.map(s => s.id)) + 1,
					selected: true,
					...source,
				},
			],
		}));
	},
}));

export default useSourcesStore;

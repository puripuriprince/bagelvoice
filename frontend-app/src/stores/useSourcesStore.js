import { create } from "zustand";

const useSourcesStore = create(set => ({
	sources: [
		{
			id: 1,
			name: "slides 1",
			selected: true,
		},
		{
			id: 2,
			name: "slides 2",
			selected: true,
		},
		{
			id: 3,
			name: "lecture #1 recording",
			selected: true,
		},
		{
			id: 4,
			name: "lecture #2 recording",
			selected: true,
		},
	],
	setSources: sources => set({ sources }),
	setSourceChecked: (id, checked) =>
		set(state => ({
			sources: state.sources.map(source =>
				source.id === id ? { ...source, selected: checked } : source,
			),
		})),
}));

export default useSourcesStore;

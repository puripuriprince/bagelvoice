import SourceItem from "./SourceItem";

export default function SourceList({ sources }) {
	return (
		<div className="grid grid-cols-1 gap-4 mt-4">
			{sources.map(source => (
				<SourceItem key={source.id} source={source} />
			))}
		</div>
	);
}

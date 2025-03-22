import BoothItem from "./BoothItem";

export default function BoothList({ booths }) {
	return (
		<div className="grid grid-cols-3 gap-4 mt-6">
			{booths.map(booth => (
				<BoothItem key={booth.id} booth={booth} />
			))}
		</div>
	);
}

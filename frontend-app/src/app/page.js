"use client";

import { Button } from "@/components/ui/button";
import useBoothStore from "@/stores/useBoothStore";
import { ClipboardIcon, PlusCircleIcon, PlusIcon } from "lucide-react";
import BoothList from "./BoothList";

export default function Home() {
	const booths = useBoothStore(state => state.booths);

	return (
		<>
			<div className="p-12">
				<h1 className="text-4xl font-bold">BagelVoice</h1>
				<p className="mt-1 text-white/50">
					Welcome to BagelVoice, the AI tutor who talks to you
				</p>
				<hr className="my-6" />
				<div className="flex items-center justify-between">
					<div className="flex items-center">
						<ClipboardIcon
							size={24}
							className="inline-block mr-2"
						/>
						<h2 className="text-2xl font-bold">Your Booths</h2>
					</div>
					<Button>
						<div className="flex items-center">
							<PlusCircleIcon
								size={24}
								className="inline-block mr-2"
							/>
							Create Booth
						</div>
					</Button>
				</div>
				{booths.length === 0 ? (
					<p className="mt-1 text-white/50">
						You do not have booths yet. Create one to get started.
					</p>
				) : (
					<BoothList booths={booths} />
				)}
			</div>
		</>
	);
}

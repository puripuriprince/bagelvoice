"use client";

import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
	DialogFooter,
	DialogClose,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import useBoothStore from "@/stores/useBoothStore";
import { ClipboardIcon, PlusCircleIcon, PlusIcon } from "lucide-react";
import BoothList from "./BoothList";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function Home() {
	const booths = useBoothStore(state => state.booths);
	const createBooth = useBoothStore(state => state.createBooth);

	const [newBoothName, setNewBoothName] = useState("");

	function onCreateBooth() {
		if (!newBoothName) return;

		createBooth({
			name: newBoothName,
		});
	}

	return (
		<>
			<div className="p-12">
				<h1 className="text-4xl font-bold">AICademy</h1>
				<p className="mt-1 text-white/50">
					Welcome to AICademy, the AI tutor who talks to you
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

					<Dialog onOpenChange={x => !x && setNewBoothName("")}>
						<DialogTrigger asChild>
							<Button>
								<div className="flex items-center">
									<PlusCircleIcon
										size={24}
										className="inline-block mr-2"
									/>
									Create Booth
								</div>
							</Button>
						</DialogTrigger>

						<DialogContent>
							<DialogHeader>
								<DialogTitle>Create a new booth</DialogTitle>
								<DialogDescription>
									Enter a name for your booth
									<Input
										className="mt-2"
										placeholder="Booth Name"
										value={newBoothName}
										onChange={e =>
											setNewBoothName(e.target.value)
										}
									/>
								</DialogDescription>
								<DialogFooter>
									<DialogClose asChild>
										<Button
											className="w-full"
											onClick={onCreateBooth}
										>
											Create
										</Button>
									</DialogClose>
								</DialogFooter>
							</DialogHeader>
						</DialogContent>
					</Dialog>
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

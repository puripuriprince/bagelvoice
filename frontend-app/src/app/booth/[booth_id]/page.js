"use client";
import { Button } from "@/components/ui/button";

import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import useSourcesStore from "@/stores/useSourcesStore";
import {
	Bars3Icon,
	DocumentIcon,
	DocumentPlusIcon,
	MicrophoneIcon,
} from "@heroicons/react/24/outline";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";

import { NewspaperIcon, PaperclipIcon, PhoneIcon } from "lucide-react";
import SourceList from "./SourceList";
import { useParams, useRouter } from "next/navigation";
import useBoothStore from "@/stores/useBoothStore";
import ImportDocument from "./ImportDocument";
import ImportText from "./ImportText";
import ImportMicrophone from "./ImportMicrophone";
import { Textarea } from "@/components/ui/textarea";

export default function BoothPage() {
	const { booth_id } = useParams();
	const sources = useSourcesStore(state => state.sources);
	const booth = useBoothStore(state =>
		state.booths.find(x => x.id === parseInt(booth_id)),
	);

	return (
		<div className="h-full flex flex-col">
			<h1 className="border-b p-6 flex items-center gap-6 text-2xl font-bold">
				<Bars3Icon className="w-8 h-8" />
				{booth.name}
			</h1>
			<div className="flex grow">
				<div className="border-e w-xs">
					<div className="flex items-center justify-between ps-6 pe-3 py-3 border-b">
						<h2 className="font-bold text-xl flex items-center gap-2">
							<PaperclipIcon className="w-6 h-6 " />
							Sources
						</h2>
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button>
									<DocumentPlusIcon size={16} />
								</Button>
							</DropdownMenuTrigger>

							<DropdownMenuContent>
								<ImportDocument />
								<ImportText />
								<ImportMicrophone />
							</DropdownMenuContent>
						</DropdownMenu>
					</div>
					<div className="px-6 mt-2">
						<p className="text-white/50">
							Select the sources to include
						</p>
						{sources.length === 0 ? (
							<div></div>
						) : (
							<SourceList sources={sources} />
						)}
					</div>
				</div>
				<div className="grow flex flex-col">
					<div className="grow"></div>
					<div className="min-h-10 w-full p-4 flex gap-2">
						<Textarea className="grow h-full" />
						<Button className={"w-20 h-full"}>
							<PaperAirplaneIcon className="w-6 h-6" />
						</Button>
					</div>
				</div>
				<div className="border-s p-6 min-w-xs">
					<div className="font-bold text-xl">
						<h2 className="font-bold text-xl flex items-center gap-2">
							<PhoneIcon className="w-6 h-6 " />
							Voice Call
						</h2>
					</div>
				</div>
			</div>
		</div>
	);
}

import { MicrophoneIcon, StopIcon } from "@heroicons/react/24/outline";
import {
	Dialog,
	DialogTrigger,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogDescription,
	DialogFooter,
	DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { DropdownMenuItem } from "@radix-ui/react-dropdown-menu";

export default function ImportMicrophone() {
	const [audioFile, setAudioFile] = useState(null);

	// TODO: Upload the files
	function handleUploadFile() {}

	return (
		<Dialog>
			<DialogTrigger
				className="flex gap-2 items-center text-sm ps-2 py-1 cursor-pointer"
				asChild
			>
				<DropdownMenuItem onSelect={e => e.preventDefault()}>
					<MicrophoneIcon className="w-4 h-4" />
					From Microphone / Recording
				</DropdownMenuItem>
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Import from Sound</DialogTitle>
					<DialogDescription>
						Select an audio file if you want to use a recording
					</DialogDescription>
					<Input
						type="file"
						onChange={e => setAudioFile(e.target.files[0])}
					/>
					<Button onClick={handleUploadFile}>Upload</Button>
					<DialogDescription>
						or, start recording from your microphone
					</DialogDescription>
					<Button onClick={handleUploadFile} variant="outline">
						<MicrophoneIcon className="w-4 h-4" />
						Record
					</Button>

					{/*<Button onClick={handleUploadFile} variant="destructive">
						<StopIcon className="w-4 h-4" />
						Stop Recording
					</Button>*/}
					<p className="text-white/50">00:00</p>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}

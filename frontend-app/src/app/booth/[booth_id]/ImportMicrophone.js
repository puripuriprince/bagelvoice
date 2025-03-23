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
import { useState, useRef, useEffect } from "react";
import { DropdownMenuItem } from "@radix-ui/react-dropdown-menu";
import useSourcesStore from "@/stores/useSourcesStore";

export default function ImportMicrophone() {
	const [audioFile, setAudioFile] = useState(null);
	const [isRecording, setIsRecording] = useState(false);
	const [recordingTime, setRecordingTime] = useState(0);
	const [audioBlob, setAudioBlob] = useState(null);
	const mediaRecorderRef = useRef(null);
	const chunksRef = useRef([]);
	const timerRef = useRef(null);
	const addSource = useSourcesStore(state => state.addSource);

	// Format the time as MM:SS
	const formatTime = seconds => {
		const mins = Math.floor(seconds / 60)
			.toString()
			.padStart(2, "0");
		const secs = (seconds % 60).toString().padStart(2, "0");
		return `${mins}:${secs}`;
	};

	// Start recording function
	const startRecording = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({
				audio: true,
			});
			mediaRecorderRef.current = new MediaRecorder(stream);

			mediaRecorderRef.current.ondataavailable = e => {
				if (e.data.size > 0) {
					chunksRef.current.push(e.data);
				}
			};

			mediaRecorderRef.current.onstop = () => {
				const audioData = new Blob(chunksRef.current, {
					type: "audio/wav",
				});
				setAudioBlob(audioData);
				chunksRef.current = [];

				// Create a file from the blob
				const file = new File([audioData], "recording.wav", {
					type: "audio/wav",
				});
				setAudioFile(file);
			};

			// Start recording
			mediaRecorderRef.current.start();
			setIsRecording(true);

			// Start timer
			setRecordingTime(0);
			timerRef.current = setInterval(() => {
				setRecordingTime(prevTime => prevTime + 1);
			}, 1000);
		} catch (err) {
			console.error("Error accessing microphone:", err);
			alert(
				"Error accessing your microphone. Please check your permissions.",
			);
		}
	};

	// Stop recording function
	const stopRecording = () => {
		if (mediaRecorderRef.current && isRecording) {
			mediaRecorderRef.current.stop();

			// Stop all audio tracks
			mediaRecorderRef.current.stream
				.getTracks()
				.forEach(track => track.stop());

			// Clear timer
			clearInterval(timerRef.current);
			setIsRecording(false);
		}
	};

	// Clean up on unmount
	useEffect(() => {
		return () => {
			if (timerRef.current) {
				clearInterval(timerRef.current);
			}
			if (
				mediaRecorderRef.current &&
				mediaRecorderRef.current.state === "recording"
			) {
				mediaRecorderRef.current.stop();
				mediaRecorderRef.current.stream
					.getTracks()
					.forEach(track => track.stop());
			}
		};
	}, []);

	// Handle uploading the file to the server
	const handleUploadFile = async () => {
		if (!audioFile) {
			alert("Please select or record an audio file first.");
			return;
		}

		// TODO: Handle real file upload
		setTimeout(() => {
			addSource({
				name: "Audio at " + new Date().toLocaleString().split(", ")[1],
				summary: "Audio recording",
			});
		}, 2000);

		try {
			const formData = new FormData();
			formData.append("audio", audioFile);

			const response = await fetch("/api/upload-audio", {
				method: "POST",
				body: formData,
			});

			if (response.ok) {
				const data = await response.json();
				alert("Upload successful!");
				console.log("Server response:", data);
				// Close the dialog or perform additional actions
			} else {
				throw new Error("Upload failed");
			}
		} catch (error) {
			console.error("Error uploading file:", error);
			alert("There was an error uploading your file. Please try again.");
		}
	};

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
						accept="audio/*"
						onChange={e => setAudioFile(e.target.files[0])}
					/>

					<DialogDescription className="mt-4">
						or, start recording from your microphone
					</DialogDescription>

					<div className="flex flex-col gap-2 mt-2">
						{!isRecording ? (
							<Button onClick={startRecording} variant="outline">
								<MicrophoneIcon className="w-4 h-4 mr-2" />
								Record
							</Button>
						) : (
							<Button
								onClick={stopRecording}
								variant="destructive"
							>
								<StopIcon className="w-4 h-4 mr-2" />
								Stop Recording
							</Button>
						)}
						<p
							className={
								isRecording ? "text-red-500" : "text-gray-500"
							}
						>
							{formatTime(recordingTime)}
						</p>

						{audioBlob && (
							<div className="mt-2">
								<audio
									controls
									src={URL.createObjectURL(audioBlob)}
									className="w-full"
								/>
							</div>
						)}
					</div>
				</DialogHeader>

				<DialogFooter className="mt-4">
					<DialogClose asChild>
						<Button
							onClick={handleUploadFile}
							disabled={!audioFile}
						>
							Upload
						</Button>
					</DialogClose>
					<DialogClose asChild>
						<Button variant="outline">Cancel</Button>
					</DialogClose>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

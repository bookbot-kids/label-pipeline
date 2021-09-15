<View>
  <Labels name="labels" toName="audio">
	<Label value="Sentence" />
  </Labels>
  <AudioPlus name="audio" value="$audio" zoom="true" hotkey="ctrl+enter" />
  <Header value="Provide Transcription" />
  <TextArea name="transcription" toName="audio" rows="4" perRegion="true" editable="true" maxSubmissions="1"/>
</View>
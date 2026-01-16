import React from "react";
import { PiPaperclipBold } from "react-icons/pi";
import { VscSend } from "react-icons/vsc";

export default function TextInput({
  inputText,
  setInputText,
  setSearchButton,
  textinputWidth,
  textinputContainerWidth,
  hide,
  margin,
  onKeyDown
}) {
  return (
    <div id="TextInput-Content" style={{ width: textinputContainerWidth, padding: '0px', marginBottom: margin }}>
      {hide ? null : (
        <input
          id="TextInput"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={onKeyDown}
          type="text"
          placeholder="Escribe el empleo que buscas..."
          style={{ width: textinputWidth }}
        />
      )}
      <div id="Upload-File-Icon">
        {inputText ? (
          <VscSend color="white" size={25} onClick={setSearchButton} />
        ) : (
          <PiPaperclipBold color="white" size={25} />
        )}
      </div>
      {hide ? (
        <div>
          <text>Buscando empleos...</text>
        </div>
      ) : null}
    </div>
  );
}

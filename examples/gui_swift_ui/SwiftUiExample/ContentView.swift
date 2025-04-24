//
//  ContentView.swift
//  SwiftUiExample
//

import SwiftUI

struct ContentView: View {
    private var deviceModel = DeviceModel()
    @State private var port: String = ""
    
    var body: some View {
        VStack {
            HStack {
                Image("logo")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(height: 100)
                    .padding()
                VStack(alignment: .leading) {
                    HStack{
                        Text("Status: ").bold()
                        Text(deviceModel.isConnected ? "Connected" : "Not Connected")
                    }
                    HStack{
                        Text("Device: ").bold()
                        Text(deviceModel.name ?? "")
                    }
                    HStack {
                        Text("Device ID: ").bold()
                        Text(deviceModel.deviceId ?? "")
                    }
                    HStack {
                        Text("Serial #: ").bold()
                        Text(deviceModel.serialNumber ?? "")
                    }
                    HStack {
                        Text("Firmware Version: ").bold()
                        Text(deviceModel.firmwareVersion ?? "")
                    }
                 }
            }
            HStack(alignment: .top) {
                VStack(alignment: .leading) {
                    TextField("Enter Serial Port...", text: $port)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .disabled(deviceModel.isConnected)
                    Button() {
                        Task {
                            await deviceModel.connect($port.wrappedValue)
                        }
                    } label: {
                        Text("Connect to Stage")
                            .frame(maxWidth: .infinity)
                    }
                    .disabled(deviceModel.isConnected)
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                        Button() {
                            Task {
                                await deviceModel.home()
                            }
                        } label: {
                            Text("Home")
                                .frame(maxWidth: .infinity)
                        }
                        Button() {
                            Task {
                                await deviceModel.moveMin()
                            }
                        } label: {
                            Text("Move Min")
                                .frame(maxWidth: .infinity)
                        }
                        Button() {
                            Task {
                                await deviceModel.moveMax()
                            }
                        } label: {
                            Text("Move Max")
                                .frame(maxWidth: .infinity)
                        }
                        Button() {
                            Task {
                                await deviceModel.stop()
                            }
                        } label: {
                            Text("Stop")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(!deviceModel.isConnected)
                }
                .padding()
                    .frame(maxWidth: .infinity)
                VStack(alignment: .leading) {
                    Text("Position: ")
                        .font(.title)
                        .bold()
                    HStack {
                        Text(deviceModel.position ?? "?")
                            .font(.title2)
                            .frame(minWidth: 80, alignment: .leading)
                        Text("mm")
                            .font(.title2)
                    }
                        
                }
                    .frame(maxWidth: .infinity)
            }
            HStack {
                if deviceModel.error != nil {
                    Image(systemName: "exclamationmark.circle.fill")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 20)
                        .foregroundColor(Color(.systemRed))
                    Text(deviceModel.error!)
                }
            }
            .frame(minHeight: 20)
        }
        .padding()
    }
}

#Preview {
    ContentView()
}

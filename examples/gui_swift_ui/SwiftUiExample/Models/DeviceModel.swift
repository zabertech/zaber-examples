//
//  DeviceModel.swift
//  SwiftUiExample
//

import Foundation
import Combine
import SwiftUI

import ZaberMotion
import ZaberMotionAscii
import ZaberMotionExceptions

enum AppError: Error {
    case notConnectedError(String)
}

enum DeviceConstants {
    static let deviceAddress = 1
    static let axisNumber = 1
}

@MainActor
@Observable
final class DeviceModel: Sendable {
    var connection: Connection?
    
    var isConnected: Bool{
        get {
            return connection != nil
        }
    }
    
    var device: Device {
        get throws {
            guard let device = try connection?.getDevice(deviceAddress: DeviceConstants.deviceAddress) else {
                throw AppError.notConnectedError("Not connected!")
            }
            return device
        }
    }
    
    var axis: ZaberMotionAscii.Axis {
        get throws {
            return try device.getAxis(axisNumber: DeviceConstants.axisNumber)
        }
    }
    
    var name: String?
    var deviceId: String?
    var serialNumber: String?
    var firmwareVersion: String?
    var position: String?
    var error: String?
    
    func connect(_ port: String) async -> Void {
        await tryCommand {
            connection = try await Connection.openSerialPort(portName: port)
            
            _ = try await device.identify()
            
            try populateIdentity()
            
            Task {
                while true {
                    do {
                        position = String(format: "%.3f", try await axis.getPosition(unit: Units.Length.mm))
                        try? await Task.sleep(nanoseconds: 100_000_000) // 100ms
                    } catch let e as MotionLibException {
                        position = nil
                        error = e.toString()
                        try? await Task.sleep(nanoseconds: 1000_000_000) // 1000ms
                    }
                }
            }
        }
    }
    
    func home() async -> Void {
        await tryCommand {
            try await axis.home(waitUntilIdle: false)
        }
    }
    
    func moveMin() async -> Void {
        await tryCommand {
            try await axis.moveMin(waitUntilIdle: false)
        }
    }
    
    func moveMax() async -> Void {
        await tryCommand {
            try await axis.moveMax(waitUntilIdle: false)
        }
    }
    
    func stop() async -> Void {
        await tryCommand {
            try await axis.stop(waitUntilIdle: false)
        }
    }
    
    private func tryCommand(_ command: () async throws -> Void) async {
        do {
            try await command()
            self.error = nil
        } catch let e as MotionLibException {
            self.error = e.toString()
        } catch {
            self.error = "Error: \(error)"
        }
    }
    
    private func populateIdentity() throws -> Void {
        let identity = try device.identity
        name = identity.name
        deviceId = String(identity.deviceId)
        serialNumber = String(identity.serialNumber)
        firmwareVersion = "\(identity.firmwareVersion.major).\(identity.firmwareVersion.minor)"
    }
}

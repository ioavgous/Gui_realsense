#!/usr/bin/env python3
import pyrealsense2 as rs
import numpy as np
import cv2


class Camera:
    def __init__(self):
        # Configure depth and color streams

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.deactivate = False
        self.image_captured = None
        # Get device product line for setting a supporting resolution
        self.pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        self.pipeline_profile = self.config.resolve(self.pipeline_wrapper)
        self.device = self.pipeline_profile.get_device()
        device_product_line = str(self.device.get_info(rs.camera_info.product_line))

        found_rgb = False
        for s in self.device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            print("Cannot start color stream")
            exit(0)

        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)

    def color_stream(self):
        self.pipeline.start(self.config)
        try:
            while True:
                # Wait for a coherent pair of frames: depth and color
                if self.deactivate is True:
                    cv2.destroyAllWindows()
                    self.pipeline.stop()
                    break
                frames = self.pipeline.wait_for_frames()

                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                if not color_frame or not depth_frame:
                    continue
                else:
                    # Convert images to numpy arrays
                    depth_image = np.asanyarray(depth_frame.get_data())
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                    color_image = cv2.resize(np.asanyarray(color_frame.get_data()), (600,400), None, None, None, cv2.INTER_AREA)

                    for width in range(0, 4):  # split image into image patches
                        for height in range(0, 4):
                            cv2.rectangle(depth_colormap, (height * 320, width * 180),
                                          ((height + 1) * 320, (width + 1) * 180), (255, 255, 255),
                                          1)  # draw a rectangle for debuggin purposes


                    # Show images
                    cv2.imshow('Depth Stream', depth_colormap)
                    cv2.imshow('Color Stream',color_image)
                    cv2.waitKey(1)
                    self.image_captured = depth_colormap

        finally:
            print("...")

    def stop_pipeline(self):
        self.pipeline.stop()

    def single_shot(self):
        # Start streaming
        self.pipeline.start(self.config)
        # Wait for a coherent pair of frames: depth and color
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

            # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        depth_colormap_dim = depth_colormap.shape
        color_colormap_dim = color_image.shape

            # If depth and color resolutions are different, resize color image to match depth image for display
        if depth_colormap_dim != color_colormap_dim:
            resized_color_image = cv2.resize(color_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
            images = np.hstack((resized_color_image, depth_colormap))
        else:
            images = np.hstack((color_image, depth_colormap))

            # Show images
        # cv2.namedWindow('Single Shot', cv2.WINDOW_AUTOSIZE)
        # cv2.imshow('RealSense', images)
        # cv2.waitKey(1)
        return depth_colormap

    def draw_rectangules(self,image):
        for width in range(0, 4):  # split image into image patches
            for height in range(0, 4):
                cv2.rectangle(image,(height*159, width*119), ((height+1)*159, (width+1)*119), (255, 255, 255), 1) # draw a rectangle for debuggin purposes
        return image

if __name__ == "__main__":
    camera = Camera()
    # camera.single_shot()
    camera.color_stream()
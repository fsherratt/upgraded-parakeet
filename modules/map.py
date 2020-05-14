import numpy as np
from scipy import interpolate
from scipy import io

class mapper:
    num_coordinate = 3

    xRange = [-20, 20]
    yRange = [-20, 20]
    zRange = [-20, 5]

    localMapRange = 10

    voxelSize = 0.5
    voxelMaxWeight = 2000
    voxelWeightDecay = 40

    xDivisions = int((xRange[1] - xRange[0]) / voxelSize)
    yDivisions = int((yRange[1] - yRange[0]) / voxelSize)
    zDivisions = int((zRange[1] - zRange[0]) / voxelSize)

    def __init__(self):
        self.xBins = np.linspace(self.xRange[0], self.xRange[1], self.xDivisions)
        self.yBins = np.linspace(self.yRange[0], self.yRange[1], self.yDivisions)
        self.zBins = np.linspace(self.zRange[0], self.zRange[1], self.zDivisions)

        self.grid = np.zeros((self.xDivisions, self.yDivisions, self.zDivisions), dtype=np.int16)

        self.interpFunc = interpolate.RegularGridInterpolator( (self.xBins, self.yBins, self.zBins),
                                                               self.grid, method = 'linear',
                                                               bounds_error = False,
                                                               fill_value = np.nan )

    # --------------------------------------------------------------------------
    # frame_to_global_points
    # param frame - (3,X,Y) matrix of coordinates from d435 camera
    # param pos - [x,y,z] offset cooridnates
    # param r - scipy local->global rotation object
    # return Null
    # --------------------------------------------------------------------------
    def local_to_global_points(self, local_points, pos, r):
        # Transform into global coordinate frame
        points_global = r.apply(local_points)
        points_global = np.add(points_global, pos)

        return points_global

    # --------------------------------------------------------------------------
    # updateMap
    # param pos - (N,3) list of points to add to the map
    # param rot -
    # return Null
    # --------------------------------------------------------------------------
    def update(self, points, pos, rot):
        # Add to map
        points = self.local_to_global_points(points, pos, rot)     
        self.updateMap(points, pos)
        self.interpFunc.values = self.grid

    def digitizePoints(self, points):
        xSort = np.digitize(points[:, 0], self.xBins) -1
        ySort = np.digitize(points[:, 1], self.yBins) -1
        zSort = np.digitize(points[:, 2], self.zBins) -1

        return [xSort, ySort, zSort]

    # --------------------------------------------------------------------------
    # updateMap
    # param points - (N,3) list of points to qadd to the map
    # return Null
    # --------------------------------------------------------------------------
    def updateMap(self, points, pos):
        # Update map
        gridPoints = self.digitizePoints(points)
        np.add.at(self.grid, gridPoints, 2)

        try:
            np.add.at(self.grid, gridPoints + np.asarray([0,0,1]), 1)
            np.add.at(self.grid, gridPoints - np.asarray([0,0,1]), 1)
        except:
            pass

        try:
            np.add.at(self.grid, gridPoints + np.asarray([0,1,0]), 1)
            np.add.at(self.grid, gridPoints - np.asarray([0,1,0]), 1)
        except:
            pass

        try:
            np.add.at(self.grid, gridPoints + np.asarray([1,0,0]), 1)
            np.add.at(self.grid, gridPoints - np.asarray([1,0,0]), 1)
        except:
            pass

        activeGridCorners = np.asarray([pos - np.asarray([self.localMapRange,
                                               self.localMapRange,
                                               self.localMapRange]),
                                        pos + np.asarray([self.localMapRange,
                                               self.localMapRange,
                                               self.localMapRange])])
        activeGridCorners = self.digitizePoints(activeGridCorners)

        activeGrid = self.grid[activeGridCorners[0][0]:activeGridCorners[0][1],
                     activeGridCorners[1][0]:activeGridCorners[1][1],
                     activeGridCorners[2][0]:activeGridCorners[2][1]]

        activeGrid = np.where(activeGrid < self.voxelMaxWeight,
                              activeGrid - self.voxelWeightDecay,  # If True
                              activeGrid)  # If False
        activeGrid = np.clip(activeGrid, a_min=0, a_max=self.voxelMaxWeight)

        self.grid[activeGridCorners[0][0]:activeGridCorners[0][1],
        activeGridCorners[1][0]:activeGridCorners[1][1],
        activeGridCorners[2][0]:activeGridCorners[2][1]] = activeGrid

        self.interpFunc.values = self.grid

    # --------------------------------------------------------------------------
    # queryMap
    # param queryPoints - (N,3) list of points to query against map
    # return (N) list of risk for each point
    # --------------------------------------------------------------------------
    def queryMap(self, queryPoints):
        return self.interpFunc(queryPoints)

    def saveToMatlab(self, filename):
        io.savemat(filename, mdict=dict(map=self.grid), do_compression=False)


class sitlMapper:
    def __init__(self):
        xRange = [-20, 20]
        yRange = [-20, 20]
        zRange = [-10, 0]

        xDivisions = 201
        yDivisions = 201
        zDivisions = 51

        self.xBins = np.linspace(xRange[0], xRange[1], xDivisions)
        self.yBins = np.linspace(yRange[0], yRange[1], yDivisions)
        self.zBins = np.linspace(zRange[0], zRange[1], zDivisions)

        self.posOld = np.asarray([0, 0, 0])
        self.grid = np.zeros((xDivisions, yDivisions, zDivisions))

        # Add Obstacle
        # north east down

        # self.grid[20, :, 5:14] = 1
        map_on = 0
        obstacle = 1
        if map_on == 1:
            self.grid[10:12, 3:11, 0:12] = obstacle  # 1
            self.grid[7:18, 14:17, :] = obstacle  # 2
            self.grid[18:20, 6:19, :] = obstacle  # 3
            self.grid[25:28, 0:12, 8:20] = obstacle  # 4
            self.grid[28:41, 17:20, :] = obstacle  # 5
            self.grid[28:31, 26:41, 0:12] = obstacle  # 6
            self.grid[0:14, 24:26, 5:15] = obstacle  # 7
            self.grid[18:20, 23:36, :] = obstacle  # 8

            self.grid[10:12, 3:11, :] = obstacle  # 1
            self.grid[25:28, 0:12, :] = obstacle  # 4
            self.grid[28:31, 26:41, :] = obstacle  # 6
            self.grid[0:14, 24:26, :] = obstacle  # 7

        if map_on == 2:
            self.grid[:29, :2, :] = obstacle  # 1
            self.grid[10:29, 5:9, :] = obstacle  # 2
            self.grid[28:39, 8:11, :] = obstacle  # 3
            self.grid[36, 8:39, :] = obstacle  # 4
            self.grid[9:27, 13:16, :] = obstacle  # 5
            self.grid[15:32, 28:, :] = obstacle  # 6

        self.interpFunc = interpolate.RegularGridInterpolator((self.xBins, self.yBins, self.zBins),
                                                              self.grid, method='linear',
                                                              bounds_error=False,
                                                              fill_value=np.nan)

    # could try nearest interp method = 'nearest' -faster but at what cost

    # --------------------------------------------------------------------------
    # queryMap
    # param queryPoints - (N,3) list of points to query against map
    # return (N) list of risk for each point
    # --------------------------------------------------------------------------
    def queryMap(self, queryPoints):
        return self.interpFunc(queryPoints)


if __name__ == "__main__":

    from modules.realsense import t265, d435
    from modules import telemetry

    import cv2
    import base64
    import time
    import threading

    t265Obj = t265.rs_t265()
    d435Obj = d435.rs_d435(framerate=30, width=480, height=270)

    mapObj = mapper()

    with t265Obj, d435Obj:
        try:
            while True:
                # Get frames of data - points and global 6dof
                pos, r, _ = t265Obj.getFrame()
                print(pos)

                starttime = time.time()
                frame, rgbImg = d435Obj.getFrame()
                points = d435Obj.deproject_frame(frame)
                mapObj.update(points, pos,r)
                
                try:
                    posGridCell = mapObj.digitizePoints(pos[np.newaxis,:])
                    starttime = time.time()

                    gridMax = np.max(mapObj.grid[:, :, posGridCell[2]])
                    if gridMax > 0:
                        grid = mapObj.grid[:, :, posGridCell[2]] / gridMax
                    else:
                        grid = mapObj.grid[:, :, posGridCell[2]]

                    empty = np.zeros((mapObj.xDivisions, mapObj.yDivisions))

                    img = cv2.merge((grid, empty, empty))
                    img = cv2.transpose(img)

                    x = np.digitize(pos[0], mapObj.xBins) - 1
                    y = np.digitize(pos[1], mapObj.yBins) - 1

                    img = cv2.circle(img, (x, y), 5, (0, 1, 0), 2)

                    vec = np.asarray([20, 0, 0])
                    vec = r.apply(vec)  # Aero-ref -> Aero-body
                    vec = vec[0]

                    vec[0] += x
                    vec[1] += y

                    img = cv2.line(img, (x, y), (int(vec[0]), int(vec[1])), (0, 0, 1), 2)

                    depth = cv2.applyColorMap(cv2.convertScaleAbs(frame, alpha=0.03), cv2.COLORMAP_JET)

                    cv2.imshow('frame', depth)
                    cv2.imshow('map', img )
                    cv2.waitKey(1)

                    # time.sleep(0.5)
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    pass

        except KeyboardInterrupt:
            pass

    # mapObj.saveToMatlab( 'TestMap.mat' )
